def inject_placeholder(payload: dict, config: dict) -> dict:
    """
    Ganti %h, %i, %m, %p dengan nilai dari config
    """
    marker = config.get("marker", "uhcx123")
    attacker_domain = config.get("attacker_domain", "uhcxispoisoning.com")
    attacker_ip = config.get("attacker_ip", "127.0.0.1")
    port = str(config.get("port", 80))

    return {
        k: v.replace("%h", attacker_domain)
             .replace("%i", attacker_ip)
             .replace("%m", marker)
             .replace("%p", port)
        for k, v in payload.items()
    }
