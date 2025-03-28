import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
CONFIG = {
    'DEFAULT_PROXY_HOST': os.getenv('PROXY_HOST', 'proxy-se1.alcom.ax'),
    'DEFAULT_PROXY_USER': os.getenv('PROXY_USER', 'kalejdo'),
    'DEFAULT_KEY_PATH': os.getenv('SSH_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa')),
    'COMMAND_TIMEOUT': 30,  # seconds
    'CONNECTION_TIMEOUT': 10,  # seconds
    'AVAILABLE_COMMANDS': {
        'ping': {
            'name': 'Ping Test',
            'description': 'Test connectivity to STB',
            'command': 'ping -c 4 {ip}'
        },
        'multicast': {
            'name': 'Multicast Test',
            'description': 'Test multicast streaming',
            'command': 'toish ms playuri udp://224.0.225.154:1234'
        },
        'reboot': {
            'name': 'Reboot STB',
            'description': 'Restart the STB',
            'command': 'reboot'
        },
        'standby': {
            'name': 'Standby Control',
            'description': 'Check and control standby mode',
            'commands': [
                'toish is getobject var.standby.mode',
                'toish ps setstandby false'
            ]
        }
    }
}
