# reactpyUI.py
"""
ReactPy UI for the AI Chat App.

- Uses the FastAPI `app` from apibridge.py
- Calls backend functions exposed via apibridge (FastAPI side) which in turn
  use backend.AIClass.
- UI implements the "Chat Controls" popup and chat layout described in Readme.md.
- If `apibridge.chat` is not yet implemented, it falls back to `health_check`
  so you can run & see the UI immediately.

Run:
    uvicorn apibridge:app --reload

(reactpyUI only defines components and attaches them to the existing app)
"""

import uuid
from typing import Any, Dict, List

import apibridge as API  # uses the same module as FastAPI bridge
from apibridge import app  # FastAPI app instance

from reactpy import component, html, hooks
from reactpy.backend.fastapi import configure


# ---------------------------------------------------------------------------
# Helper components
# ---------------------------------------------------------------------------

def _base_container_style():
    return {
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "minHeight": "100vh",
        "backgroundColor": "#f5f5f7",  # light grey like in screenshot
        "fontFamily": "-apple-system, system-ui, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
        "padding": "24px",
        "boxSizing": "border-box",
    }


def _card_style():
    return {
        "width": "100%",
        "maxWidth": "800px",
        "backgroundColor": "#ffffff",
        "borderRadius": "24px",
        "boxShadow": "0 18px 45px rgba(15,23,42,0.12)",
        "padding": "20px 20px 16px 20px",
        "boxSizing": "border-box",
        "display": "flex",
        "flexDirection": "column",
        "gap": "12px",
    }


def _pill_button_style(primary: bool = False):
    if primary:
        bg = "#4f46e5"  # indigo-ish purple (like toggles in screenshot)
        color = "#ffffff"
    else:
        bg = "#f3f4f6"
        color = "#111827"
    return {
        "borderRadius": "999px",
        "border": "none",
        "padding": "8px 16px",
        "fontSize": "14px",
        "cursor": "pointer",
        "backgroundColor": bg,
        "color": color,
        "display": "flex",
        "alignItems": "center",
        "gap": "8px",
    }


@component
def ToggleRow(label: str, description: str, value: bool, on_change):
    """A single row in the Chat Controls popup."""
    def handle_change(event):
        checked = event["target"]["checked"]
        on_change(checked)

    return html.div(
        {
            "style": {
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "12px",
                "gap": "12px",
            }
        },
        html.div(
            {
                "style": {
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "2px",
                }
            },
            html.span({"style": {"fontWeight": "600", "fontSize": "14px"}}, label),
            html.span({"style": {"fontSize": "12px", "color": "#6b7280"}}, description),
        ),
        html.input(
            {
                "type": "checkbox",
                "checked": value,
                "on_change": handle_change,
                "style": {
                    "width": "42px",
                    "height": "22px",
                    "accentColor": "#4f46e5",
                    "cursor": "pointer",
                },
            }
        ),
    )


@component
def ChatControlsPopup(settings: Dict[str, bool], on_update_setting):
    """The floating Chat Controls card (like the screenshot)."""
    return html.div(
        {
            "style": {
                "position": "absolute",
                "top": "-10px",
                "right": "0",
                "transform": "translateY(-100%)",
                "backgroundColor": "#ffffff",
                "borderRadius": "24px",
                "boxShadow": "0 18px 45px rgba(15,23,42,0.16)",
                "padding": "18px 18px 14px 18px",
                "width": "260px",
                "boxSizing": "border-box",
                "zIndex": "50",
            }
        },
        html.h3(
            {
                "style": {
                    "margin": "0 0 12px 0",
                    "fontSize": "16px",
                    "fontWeight": "700",
                }
            },
            "Chat controls",
        ),
        html.p(
            {
                "style": {
                    "margin": "0 0 4px 0",
                    "fontSize": "12px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                    "color": "#9ca3af",
                    "fontWeight": "600",
                }
            },
            "Capabilities",
        ),
        ToggleRow(
            "Web Search",
            "Use tools to browse the web.",
            settings["web_search"],
            lambda v: on_update_setting("web_search", v),
        ),
        ToggleRow(
            "Image Generation",
            "Generate or edit images.",
            settings["image_generation"],
            lambda v: on_update_setting("image_generation", v),
        ),
        ToggleRow(
            "Data Analysis",
            "Analyze files and data tables.",
            settings["data_analysis"],
            lambda v: on_update_setting("data_analysis", v),
        ),
        ToggleRow(
            "Think",
            "Enhanced step-by-step reasoning.",
            settings["think"],
            lambda v: on_update_setting("think", v),
        ),
    )


@component
def MessageBubble(role: str, content: str):
    is_user = role == "user"
    align = "flex-end" if is_user else "flex-start"
    bg = "#4f46e5" if is_user else "#f3f4f6"
    color = "#ffffff" if is_user else "#111827"

    return html.div(
        {
            "style": {
                "display": "flex",
                "justifyContent": align,
                "marginBottom": "6px",
            }
        },
        html.div(
            {
                "style": {
                    "maxWidth": "75%",
                    "backgroundColor": bg,
                    "color": color,
                    "padding": "8px 12px",
                    "borderRadius": "16px",
                    "fontSize": "14px",
                    "whiteSpace": "pre-wrap",
                }
            },
            content,
        ),
    )


# ---------------------------------------------------------------------------
# Main app component
# ---------------------------------------------------------------------------

@component
def ChatApp():
    # Messages: list of {"role": "user"/"assistant", "content": str}
    messages, set_messages = hooks.use_state([])

    # Input text
    input_text, set_input_text = hooks.use_state("")

    # Settings toggles
    settings, set_settings = hooks.use_state(
        {
            "web_search": True,
            "image_generation": True,
            "data_analysis": True,
            "think": False,
        }
    )

    # Show / hide chat controls popup
    show_controls, set_show_controls = hooks.use_state(False)

    # Session id shared with backend (for RAG, uploads, etc.)
    session_id, _ = hooks.use_state(str(uuid.uuid4()))

    # Loading indicator
    is_sending, set_is_sending = hooks.use_state(False)

    # Placeholder list of uploaded file names (UI only)
    uploaded_files, set_uploaded_files = hooks.use_state([])

    # ----------------------- event handlers -------------------------------

    def on_change_input(event):
        set_input_text(event["target"]["value"])

    def on_update_setting(key: str, value: bool):
        def updater(prev):
            new_settings = dict(prev)
            new_settings[key] = value
            return new_settings
        set_settings(updater)

    def on_toggle_controls(event):
        set_show_controls(lambda prev: not prev)

    def on_files_selected(event):
        # NOTE: ReactPy currently does not give direct file content here;
        # this is just a UI list of file names. Real upload should go
        # through a dedicated FastAPI endpoint with <form enctype="multipart/form-data">.
        file_list = event["target"]["files"]
        names = [f["name"] for f in file_list] if file_list else []
        if not names:
            return

        def updater(prev):
            return prev + names

        set_uploaded_files(updater)

    def send_system_message(text: str):
        """Convenience helper to show system-ish messages from the UI."""
        def updater(prev):
            return prev + [{"role": "assistant", "content": text}]
        set_messages(updater)

    async def on_send_message(event):
        nonlocal input_text

        text = input_text.strip()
        if not text or is_sending:
            return

        # Append user message locally
        user_msg = {"role": "user", "content": text}
        def add_user(prev):
            return prev + [user_msg]
        set_messages(add_user)
        set_input_text("")
        set_is_sending(True)

        # Prepare payload for backend (matches README structure)
        request_payload: Dict[str, Any] = {
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in (messages + [user_msg])
            ],
            "settings": settings,
            "session_id": session_id,
        }

        try:
            # Python içinden doğrudan FastAPI fonksiyonunu çağırıyoruz
            chat_response = API.chat(request_payload)

            # apibridge.chat -> {"response": "..."}
            content = chat_response.get("response", "")
            if not content:
                content = "Backend returned an empty response."

            reply = {"role": "assistant", "content": content}

        except Exception as e:  # noqa: BLE001
            reply = {
                "role": "assistant",
                "content": f"Error while calling backend: {type(e).__name__}: {e}",
            }


        def add_assistant(prev):
            return prev + [reply]

        set_messages(add_assistant)
        set_is_sending(False)

    async def on_health_check(event):
        try:
            hc = API.health_check()
            txt = hc.get("result", str(hc))
        except Exception as e:  # noqa: BLE001
            txt = f"Health check failed: {type(e).__name__}: {e}"
        send_system_message(f"[Health check]\n{txt}")

    # ----------------------------- render --------------------------------

    return html.div(
        {"style": _base_container_style()},
        html.div(
            {"style": _card_style()},
            # Header row
            html.div(
                {
                    "style": {
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "4px",
                    }
                },
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "2px",
                        }
                    },
                    html.span(
                        {"style": {"fontWeight": "700", "fontSize": "18px"}},
                        "AI Chat",
                    ),
                    html.span(
                        {"style": {"fontSize": "12px", "color": "#6b7280"}},
                        "Tool-calling chat with RAG, web search, images & data analysis.",
                    ),
                ),
                html.button(
                    {
                        "style": _pill_button_style(False),
                        "on_click": on_health_check,
                    },
                    "Check health",
                ),
            ),

            # Messages area
            html.div(
                {
                    "style": {
                        "flex": "1 1 auto",
                        "minHeight": "260px",
                        "maxHeight": "400px",
                        "overflowY": "auto",
                        "borderRadius": "16px",
                        "backgroundColor": "#f9fafb",
                        "padding": "12px 12px 8px 12px",
                        "boxSizing": "border-box",
                    }
                },
                [
                    MessageBubble(m["role"], m["content"])
                    for m in messages
                ]
                or html.div(
                    {
                        "style": {
                            "fontSize": "13px",
                            "color": "#9ca3af",
                        }
                    },
                    "Ask anything, or upload files below and enable capabilities in Chat Controls.",
                ),
            ),

            # Uploaded files preview (just names for now)
            html.div(
                {
                    "style": {
                        "fontSize": "12px",
                        "color": "#6b7280",
                        "marginTop": "2px",
                        "minHeight": "16px",
                    }
                },
                (
                    "Files: "
                    + ", ".join(uploaded_files)
                )
                if uploaded_files
                else "",
            ),

            # Bottom controls: Add file + Settings + Chat input
            html.div(
                {
                    "style": {
                        "position": "relative",
                        "marginTop": "8px",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "8px",
                    }
                },
                # Row with Add file + Settings
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "justifyContent": "space-between",
                            "alignItems": "center",
                            "gap": "8px",
                        }
                    },
                    html.label(
                        {
                            "style": _pill_button_style(False)
                            | {"cursor": "pointer"},
                        },
                        "Add file",
                        html.input(
                            {
                                "type": "file",
                                "multiple": True,
                                "style": {"display": "none"},
                                "on_change": on_files_selected,
                            }
                        ),
                    ),
                    html.div(
                        {
                            "style": {
                                "position": "relative",
                            }
                        },
                        html.button(
                            {
                                "style": _pill_button_style(False),
                                "on_click": on_toggle_controls,
                            },
                            "Settings",
                        ),
                        ChatControlsPopup(settings, on_update_setting)
                        if show_controls
                        else None,
                    ),
                ),

                # Chat input row
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "alignItems": "center",
                            "gap": "8px",
                        }
                    },
                    html.textarea(
                        {
                            "value": input_text,
                            "on_change": on_change_input,
                            "rows": 2,
                            "placeholder": "Send a message...",
                            "style": {
                                "flex": "1 1 auto",
                                "resize": "none",
                                "fontSize": "14px",
                                "padding": "8px 10px",
                                "borderRadius": "999px",
                                "border": "1px solid #e5e7eb",
                                "outline": "none",
                            },
                        }
                    ),
                    html.button(
                        {
                            "style": _pill_button_style(True),
                            "on_click": on_send_message,
                            "disabled": is_sending or not input_text.strip(),
                        },
                        "Send",
                    ),
                ),
            ),
        ),
    )


# Attach ReactPy root component to the existing FastAPI app
configure(app, ChatApp)
