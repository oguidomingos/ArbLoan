import os
import sys
import json
import logging
import structlog
from pathlib import Path
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Gauge, start_http_server
from typing import Optional
from slack_sdk import WebClient
from telegram.ext import ApplicationBuilder

# Métricas Prometheus
OPPORTUNITIES = Counter('arb_opportunities_total', 'Total de oportunidades detectadas')
TRADES = Counter('arb_trades_total', 'Total de trades executados')
PROFIT = Gauge('arb_profit_total', 'Lucro total em USD')
API_LATENCY = Gauge('api_latency_seconds', 'Latência das chamadas à API')

class ArbLogger:
    def __init__(self):
        # Criar diretório de logs se não existir
        Path("logs").mkdir(exist_ok=True)
        
        # Configurar logging estruturado
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(os.getenv("LOG_FILE", "logs/arbitrage.log"))
            ]
        )

        # Configurar structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.render_to_log_kwargs,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger()
        
        # Configurar notificações
        self.slack_client = self._setup_slack() if os.getenv("SLACK_WEBHOOK_URL") else None
        self.telegram_app = self._setup_telegram() if os.getenv("TELEGRAM_BOT_TOKEN") else None

    def _setup_slack(self) -> Optional[WebClient]:
        """Configura cliente Slack se webhook URL fornecida"""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            return WebClient(token=webhook_url)
        return None

    def _setup_telegram(self) -> Optional[ApplicationBuilder]:
        """Configura cliente Telegram se token fornecido"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token:
            return ApplicationBuilder().token(bot_token).build()
        return None

    async def notify(self, message: str, level: str = "INFO"):
        """Envia notificação para Slack e Telegram configurados"""
        if self.slack_client:
            try:
                await self.slack_client.chat_postMessage(
                    channel="#arbitragem",
                    text=message
                )
            except Exception as e:
                self.logger.error("Erro ao enviar notificação Slack", error=str(e))

        if self.telegram_app and os.getenv("TELEGRAM_CHAT_ID"):
            try:
                await self.telegram_app.bot.send_message(
                    chat_id=os.getenv("TELEGRAM_CHAT_ID"),
                    text=message
                )
            except Exception as e:
                self.logger.error("Erro ao enviar notificação Telegram", error=str(e))

    def start_metrics_server(self, port: int = 9090):
        """Inicia servidor Prometheus na porta especificada"""
        try:
            start_http_server(port)
            self.logger.info(f"Servidor de métricas iniciado na porta {port}")
        except Exception as e:
            self.logger.error("Erro ao iniciar servidor de métricas", error=str(e))

    def log_opportunity(self, pair: str, profit_percent: float, gas_cost: float):
        """Registra oportunidade de arbitragem detectada"""
        OPPORTUNITIES.inc()
        self.logger.info(
            "opportunity_found",
            pair=pair,
            profit_percent=profit_percent,
            gas_cost=gas_cost
        )

    def log_trade(self, pair: str, profit_usd: float, gas_used: float):
        """Registra trade executado"""
        TRADES.inc()
        PROFIT.inc(profit_usd)
        self.logger.info(
            "trade_executed",
            pair=pair,
            profit_usd=profit_usd,
            gas_used=gas_used
        )

    def log_api_latency(self, endpoint: str, latency: float):
        """Registra latência de chamada à API"""
        API_LATENCY.labels(endpoint=endpoint).set(latency)

# Instância global do logger
arb_logger = ArbLogger()