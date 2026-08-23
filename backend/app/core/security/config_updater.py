import os

class ConfigUpdater:
    """
    Utility to securely update the .env file with master configurations,
    such as the MASTER_ENCRYPTION_KEY or global DB credentials.
    """
    def __init__(self, env_path: str = ".env"):
        self.env_path = env_path

    def update_env_variable(self, key: str, value: str):
        """
        Updates an existing variable or adds a new one in the .env file.
        """
        env_vars = self._read_env()
        env_vars[key] = value
        self._write_env(env_vars)

    def _read_env(self) -> dict:
        env_vars = {}
        if not os.path.exists(self.env_path):
            return env_vars
            
        with open(self.env_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
        return env_vars

    def _write_env(self, env_vars: dict):
        with open(self.env_path, "w") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
                
# Singleton instance
config_updater = ConfigUpdater()
