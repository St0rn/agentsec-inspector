# Modèle de sécurité

- Backend lié à `127.0.0.1` uniquement; démarrage refusé sur une adresse non loopback.
- Jeton local aléatoire par processus desktop, transmis au frontend par commande IPC Tauri.
- Origines CORS limitées; WebSocket authentifié.
- Validation Pydantic stricte, tailles maximales et contraintes de types.
- Protection SSRF par schéma, autorisation distante, résolution DNS et blocage des adresses link-local/réservées; redirections désactivées.
- Secrets de connecteurs chiffrés localement avec Fernet et clé protégée par ACL utilisateur. Sur Windows, l’ACL du répertoire utilisateur reste une composante de confiance.
- MCP passif par défaut. La découverte n’appelle jamais les outils exposés.
- MCP stdio sans shell, exécutable explicitement allowlisté, arguments bornés, environnement réduit, timeout et arrêt forcé.
- Scénarios par défaut avec marqueurs fictifs, jamais de secret réel.
- Échec de transport classé `ERROR`, jamais `FAIL` de sécurité.
- Preuves et rapports empreintés SHA-256.
- Pas d’inférence du raisonnement caché; seules traces et actions observables sont présentées.

Limite importante : un sous-processus MCP n’est pas une sandbox de sécurité. L’analyse d’un binaire non fiable doit se faire dans une VM ou Windows Sandbox administrée séparément.
