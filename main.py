#!/usr/bin/env python3
import logging
from gui import SSHApp

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('stb_tool.log'),
            logging.StreamHandler()
        ]
    )

    # Start application
    app = SSHApp()
    app.mainloop()

if __name__ == "__main__":
    main()
