"""Response-language support.

The FAQ/KB content is English, so retrieval always runs on an English query
(see query_understanding); only user-facing text is produced in the chosen
language — LLM-generated answers via `language_instruction`, and the fixed
follow-up/escalation messages via the translations below.
"""

from typing import Literal

LanguageCode = Literal["en", "ar", "fr", "pt"]

DEFAULT_LANGUAGE: LanguageCode = "en"

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ar": "Arabic",
    "fr": "French",
    "pt": "Portuguese",
}


def normalize_language(code: str | None) -> str:
    return code if code in LANGUAGE_NAMES else DEFAULT_LANGUAGE


def language_instruction(code: str | None) -> str:
    """Appended to system prompts whose output is shown to the user."""
    name = LANGUAGE_NAMES[normalize_language(code)]
    return (
        f"\n\nIMPORTANT: Write your entire response in {name}, regardless of the "
        f"language of the user's message or of the context excerpts. Keep product "
        f"names, role names, and email addresses/phone numbers as they are."
    )


# Prefix of the low-confidence follow-up message. Every translation is also
# used to recognise earlier follow-up turns in chat_history (see
# followup._consecutive_unsuccessful_attempts), so the attempt counter keeps
# working if the user switches language mid-conversation.
FOLLOWUP_PREFIXES: dict[str, str] = {
    "en": (
        "I couldn't find a fully confident answer to that yet. Here are some "
        "related questions I can help with:"
    ),
    "ar": (
        "لم أتمكن بعد من العثور على إجابة مؤكدة تمامًا لذلك. إليك بعض الأسئلة "
        "ذات الصلة التي يمكنني المساعدة فيها:"
    ),
    "fr": (
        "Je n'ai pas encore trouvé de réponse entièrement fiable à cette question. "
        "Voici quelques questions connexes sur lesquelles je peux vous aider :"
    ),
    "pt": (
        "Ainda não encontrei uma resposta totalmente segura para isso. Aqui estão "
        "algumas perguntas relacionadas com as quais posso ajudar:"
    ),
}

_ESCALATION_MESSAGES: dict[str, str] = {
    "en": (
        "Thanks for reaching out — I've escalated this to our support team, who "
        "will follow up with you shortly. You can also reach them directly at "
        "{email} or {phone}."
    ),
    "ar": (
        "شكرًا لتواصلك معنا — لقد أحلت طلبك إلى فريق الدعم لدينا، وسيتواصلون معك "
        "قريبًا. يمكنك أيضًا التواصل معهم مباشرة عبر {email} أو {phone}."
    ),
    "fr": (
        "Merci de nous avoir contactés — j'ai transmis votre demande à notre équipe "
        "d'assistance, qui reviendra vers vous rapidement. Vous pouvez également la "
        "joindre directement à {email} ou au {phone}."
    ),
    "pt": (
        "Obrigado pelo contato — encaminhei isto para a nossa equipe de suporte, que "
        "entrará em contato com você em breve. Você também pode falar diretamente "
        "com ela pelo {email} ou {phone}."
    ),
}


def followup_prefix(code: str | None) -> str:
    return FOLLOWUP_PREFIXES[normalize_language(code)]


def escalation_message(code: str | None, email: str, phone: str) -> str:
    return _ESCALATION_MESSAGES[normalize_language(code)].format(email=email, phone=phone)
