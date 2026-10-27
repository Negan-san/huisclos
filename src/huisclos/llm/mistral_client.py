"""Envoi facultatif du texte pseudonymisé au service de chat Mistral.

Entrées : texte déjà relu, consigne, clé API, modèle et délai maximal.
Sortie : réponse textuelle ou erreur explicite, sans journaliser les contenus.
Place dans le pipeline : après la revue humaine, avant la restauration locale.
"""

import requests

# URL à confirmer dans la documentation officielle, sans accès réseau en S34.
CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
# Nom de modèle à confirmer dans la documentation officielle, sans accès réseau en S34.
DEFAULT_MODEL = "mistral-small-latest"

ERROR_MESSAGES: dict[str, str] = {
    "unauthorized": "Mistral refused the API key (401). Check the configured key.",
    "quota": "Mistral quota exceeded (429). Try again later or check your quota.",
    "timeout": "Mistral did not respond before the timeout. Try again later.",
    "connection": "Mistral could not be reached. Check your connection and try again.",
    "unexpected": "Mistral returned an unexpected response. Try again later.",
}


class MistralError(ValueError):
    """Erreur publique sans contenu sensible ; code permet sa traduction par l'interface."""

    def __init__(self, code: str) -> None:
        """Conserve le code reçu et fournit un message lisible à l'appelant."""
        self.code = code
        super().__init__(ERROR_MESSAGES[code])


def send_pseudonymized(
    text: str, instruction: str, api_key: str, model: str, timeout: float = 30
) -> str:
    """Envoie le texte suivi de la consigne et renvoie la réponse du modèle.

    L'appelant fournit uniquement le texte pseudonymisé validé, jamais la table.
    Les erreurs ne reprennent ni le corps HTTP, ni les exceptions du transport.
    """
    try:
        response = requests.post(
            CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": text + instruction}]},
            timeout=timeout,
            # Une redirection ne doit pas transmettre le texte à une autre destination.
            allow_redirects=False,
        )
    except requests.Timeout:
        raise MistralError("timeout") from None
    except requests.RequestException:
        raise MistralError("connection") from None
    if response.status_code == 401:
        raise MistralError("unauthorized")
    if response.status_code == 429:
        raise MistralError("quota")
    if response.status_code != 200:
        raise MistralError("unexpected")
    try:
        answer = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise MistralError("unexpected") from None
    if not isinstance(answer, str) or not answer.strip():
        raise MistralError("unexpected")
    return answer
