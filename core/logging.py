import logging
import logging.handlers
import os
import sys
from typing import Optional, Union
from pathlib import Path
from dotenv import load_dotenv

from utils import Singleton

# Carrega variáveis do .env
load_dotenv()


@Singleton
class AppLogger:
    def __init__(self) -> None:
        """
        Inicializa o sistema de logging baseado nas configurações do .env
        """
        self._initialized = False
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configura o sistema de logging baseado nas configurações do .env"""
        if self._initialized:
            # Remove handlers existentes para evitar duplicação
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        # Obtém configurações de logging do .env
        log_level = os.getenv('LOGGING_LEVEL', 'INFO')
        log_file = os.getenv('LOGGING_FILE', 'app.log')
        max_bytes = int(os.getenv('LOGGING_MAX_BYTES', '10485760'))  # 10MB padrão
        backup_count = int(os.getenv('LOGGING_BACKUP_COUNT', '5'))
        environment = os.getenv('ENVIRONMENT', 'dev')
        log_to_console = os.getenv('LOGGING_CONSOLE', 'true').lower() == 'true'
        
        # Converte string de nível para constante do logging
        level = self._get_log_level(log_level)
        
        # Configura o logger raiz
        logger = logging.getLogger()
        logger.setLevel(level)
        
        # Cria formatter
        formatter = self._create_formatter(environment)
        
        # Handler para arquivo (com rotação)
        if log_file and log_file.lower() != 'none':
            file_handler = self._create_file_handler(log_file, max_bytes, backup_count, level, formatter)
            if file_handler:
                logger.addHandler(file_handler)
        
        # Handler para console
        if (environment.lower() in ['development', 'test', 'dev'] or 
            (environment.lower() == 'production' and log_to_console)):
            console_handler = self._create_console_handler(level, formatter)
            logger.addHandler(console_handler)
        
        # Configura logging de terceiros
        self._configure_third_party_loggers()
        
        self._initialized = True
        logging.info("Logging configurado com sucesso")
    
    def _get_log_level(self, level_str: str) -> int:
        """Converte string de nível para constante do logging"""
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        return level_map.get(level_str.lower(), logging.INFO)
    
    def _create_formatter(self, environment: str) -> logging.Formatter:
        """Cria formatter apropriado para o ambiente"""
        if environment.lower() in ['development', 'test', 'dev']:
            # Formatter mais detalhado para desenvolvimento
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            # Formatter mais simples para produção
            return logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def _create_file_handler(self, log_file: str, max_bytes: int, 
                           backup_count: int, level: int, 
                           formatter: logging.Formatter) -> Optional[logging.Handler]:
        """Cria handler para arquivo com rotação"""
        try:
            # Garante que o diretório existe
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            return file_handler
        except (OSError, IOError) as e:
            logging.error(f"Erro ao criar file handler: {e}")
            return None
    
    def _create_console_handler(self, level: int, formatter: logging.Formatter) -> logging.Handler:
        """Cria handler para console"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        return console_handler
    
    def _configure_third_party_loggers(self) -> None:
        """Configura níveis de logging para bibliotecas de terceiros"""
        third_party_loggers = {
            'urllib3': logging.WARNING,
            'github': logging.INFO,
            'requests': logging.WARNING,
            'botocore': logging.WARNING,
            'boto3': logging.WARNING,
            'sqlalchemy': logging.WARNING,
            'matplotlib': logging.WARNING
        }
        
        for logger_name, level in third_party_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Retorna um logger com o nome especificado
        
        Args:
            name: Nome do logger (se None, retorna o logger raiz)
        
        Returns:
            Instância do logger configurado
        """
        return logging.getLogger(name)
    
    def reload_config(self) -> None:
        """Recarrega as configurações e reconfigura o logging"""
        load_dotenv(override=True)
        self._setup_logging()
        logging.info("Configuração de logging recarregada")
    
    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log genérico com nível especificado"""
        self.get_logger().log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log de nível DEBUG"""
        self.get_logger().debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log de nível INFO"""
        self.get_logger().info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log de nível WARNING"""
        self.get_logger().warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log de nível ERROR"""
        self.get_logger().error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log de nível CRITICAL"""
        self.get_logger().critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log de exceção com nível ERROR"""
        self.get_logger().exception(msg, *args, **kwargs)
    
    def set_level(self, level: Union[str, int]) -> None:
        """
        Altera o nível de logging dinamicamente
        
        Args:
            level: Nível de logging (string ou constante)
        """
        if isinstance(level, str):
            level = self._get_log_level(level)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        for handler in root_logger.handlers:
            handler.setLevel(level)


# Exemplo de uso aprimorado:
if __name__ == "__main__":
    # Obtém o logger singleton
    log = AppLogger()
    
    # Exemplos de logging
    log.debug("Mensagem de debug detalhada")
    log.info("Mensagem informativa")
    log.warning("Aviso importante")
    log.error("Erro ocorreu")
    
    try:
        # Simula uma exceção
        raise ValueError("Erro de exemplo")
    except ValueError as e:
        log.exception("Exceção capturada: %s", e)
    
    # Logger específico para módulo
    app_logger = log.get_logger("meu_modulo")
    app_logger.info("Log específico do módulo com contexto adicional", 
                   extra={'user': 'john_doe', 'action': 'login'})
    
    # Alterando nível dinamicamente
    log.set_level('DEBUG')
    log.debug("Esta mensagem será exibida após mudar para DEBUG")