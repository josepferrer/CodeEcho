import logging
import sys

def setup_logging():
    """Configures logging for the entire application."""
    logging.basicConfig(
        level=logging.INFO,  # Cambia a DEBUG si necesitas más detalle
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # logging.StreamHandler(sys.stdout),  # Muestra logs en consola
            logging.FileHandler("app.log"),  # Descomenta para guardar en un fichero
        ]
    )