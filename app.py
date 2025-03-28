import dash
    import dash_bootstrap_components as dbc
    from dash import dcc, html
    from dash.dependencies import Input, Output, State
    from ssh_client import SSHClient, CommandRunner
    from config import CONFIG
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('stb_tool.log'),
            logging.StreamHandler()
        ]
    )

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Input(id="host", placeholder="Host", type="text", value=CONFIG['DEFAULT_PROXY_HOST']),
                dbc.Input(id="username", placeholder="Username", type="text", value=CONFIG['DEFAULT_PROXY_USER']),
                dbc.Input(id="key_path", placeholder="Key Path", type="text", value=CONFIG['DEFAULT_KEY_PATH']),
                dbc.Input(id="passphrase", placeholder="Passphrase", type="password"),
                dbc.Button("Connect", id="connect-button", color="primary", className="mr-1"),
                dbc.Button("Disconnect", id="disconnect-button", color="danger", className="mr-1"),
                html.Div(id="connection-status")
            ], width=6),
            dbc.Col([
                dbc.Input(id="client_ip", placeholder="Client IP", type="text"),
                dcc.Dropdown(
                    id="command",
                    options=[{"label": cmd['name'], "value": cmd_key} for cmd_key, cmd in CONFIG['AVAILABLE_COMMANDS'].items()],
                    value=list(CONFIG['AVAILABLE_COMMANDS'].keys())[0]
                ),
                dbc.Button("Execute", id="execute-button", color="success", className="mr-1"),
                dcc.Textarea(id="output", style={'width': '100%', 'height': 300})
            ], width=6)
        ])
    ])

    @app.callback(
        Output("connection-status", "children"),
        [Input("connect-button", "n_clicks"), Input("disconnect-button", "n_clicks")],
        [State("host", "value"), State("username", "value"), State("key_path", "value"), State("passphrase", "value")]
    )
    def connect_disconnect(connect_clicks, disconnect_clicks, host, username, key_path, passphrase):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == "connect-button":
            try:
                ssh_client = SSHClient(host, username, key_path, passphrase)
                ssh_client.connect()
                return f"Connected to {host}"
            except Exception as e:
                return f"Connection Error: {str(e)}"

        elif button_id == "disconnect-button":
            try:
                ssh_client.disconnect()
                return "Disconnected"
            except Exception as e:
                return f"Disconnection Error: {str(e)}"

    @app.callback(
        Output("output", "value"),
        [Input("execute-button", "n_clicks")],
        [State("client_ip", "value"), State("command", "value")]
    )
    def execute_command(n_clicks, client_ip, command):
        if n_clicks is None:
            return ""

        try:
            command_config = CONFIG['AVAILABLE_COMMANDS'].get(command)
            if not command_config:
                raise ValueError(f"Unknown command: {command}")

            if isinstance(command_config.get('command'), str):
                commands = [command_config['command']]
            else:
                commands = command_config.get('commands', [])

            command_runner = CommandRunner(ssh_client)
            outputs, logclient_output = command_runner.run_command_sequence(client_ip, commands)

            return "\n".join(outputs) + "\n" + logclient_output
        except Exception as e:
            return f"Command Error: {str(e)}"

    if __name__ == "__main__":
        app.run_server(debug=True)
