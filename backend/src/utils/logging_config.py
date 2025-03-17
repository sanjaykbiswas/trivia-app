import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app_name="trivia_app", log_dir="logs", log_level=logging.INFO):
    """
    Configure logging for the application
    
    Args:
        app_name (str): Application name for the log file
        log_dir (str): Directory to store log files
        log_level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Create formatters
    verbose_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create file handler for all logs
    log_file = os.path.join(log_dir, f"{app_name}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(verbose_formatter)
    
    # Create console handler for standard output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Create and configure app-specific logger
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(log_level)
    
    # Configure specific loggers for different modules
    for module in ["supabase_actions", "upload_service", "question_service"]:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(log_level)
        
        # Create module-specific log file
        module_log_file = os.path.join(log_dir, f"{module}.log")
        module_handler = RotatingFileHandler(
            module_log_file,
            maxBytes=5242880,  # 5MB
            backupCount=3
        )
        module_handler.setLevel(log_level)
        module_handler.setFormatter(verbose_formatter)
        
        module_logger.addHandler(module_handler)
    
    app_logger.info(f"Logging configured for {app_name}")
    
    return app_logger