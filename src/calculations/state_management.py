"""Helper module for persistent Streamlit widgets.

This module provides wrapper functions around standard Streamlit widgets
(number_input, slider, etc.) that automatically store and retrieve their
values from st.session_state['data']. This ensures that input values are
preserved when switching between different scenarios.
"""

import streamlit as st
from typing import Any, Optional


def init_session_state():
    """Initialize the session state data dictionary if it doesn't exist."""
    if "data" not in st.session_state:
        st.session_state["data"] = {}


def _get_value(key: str, default: Any) -> Any:
    """Retrieve value from session state or return default."""
    init_session_state()
    return st.session_state["data"].get(key, default)


def _on_change_handler(key: str):
    """Callback to update session state when widget changes."""
    st.session_state["data"][key] = st.session_state[key]


def persistent_number_input(
    label: str,
    min_value: float | int | None = None,
    max_value: float | int | None = None,
    value: float | int | None = None,
    step: float | int | None = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible"
) -> float | int:
    """
    Wrapper for st.number_input that persists value in st.session_state['data'].
    Matches st.number_input signature more closely.
    """
    if key is None:
        raise ValueError("Must provide 'key' for persistent_number_input")

    init_session_state()
    
    # Get current value from persistent storage or use default
    current_value = st.session_state["data"].get(key, value)
    
    # Render widget
    val = st.number_input(
        label,
        min_value=min_value,
        max_value=max_value,
        value=current_value,
        step=step,
        format=format,
        key=key,
        help=help,
        on_change=_on_change_handler,
        args=(key,),
        disabled=disabled,
        label_visibility=label_visibility
    )
    
    # Sync immediately
    st.session_state["data"][key] = val
    return val


def persistent_slider(
    label: str,
    min_value: float | int | None = None,
    max_value: float | int | None = None,
    value: float | int | tuple | None = None,
    step: float | int | None = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible"
) -> float | int | tuple:
    """
    Wrapper for st.slider that persists value in st.session_state['data'].
    Matches st.slider signature more closely to allow positional args.
    """
    if key is None:
        raise ValueError("Must provide 'key' for persistent_slider")
        
    init_session_state()
    
    # "value" acts as the default if not in state
    current_value = st.session_state["data"].get(key, value)
    
    val = st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=current_value,
        step=step,
        format=format,
        key=key,
        help=help,
        on_change=_on_change_handler,
        args=(key,),
        disabled=disabled,
        label_visibility=label_visibility
    )
    
    st.session_state["data"][key] = val
    return val


def persistent_radio(
    label: str,
    options: list,
    key: str,
    index: int = 0,
    **kwargs
) -> str:
    """
    Wrapper for st.radio that persists value in st.session_state['data'].
    """
    init_session_state()
    
    # Default value is the option at the given index
    default_val = options[index] if 0 <= index < len(options) else options[0]
    
    saved_val = st.session_state["data"].get(key, default_val)
    
    # Find index of saved value
    try:
        current_index = options.index(saved_val)
    except ValueError:
        current_index = index

    val = st.radio(
        label,
        options,
        index=current_index,
        key=key,
        on_change=_on_change_handler,
        args=(key,),
        **kwargs
    )
    
    st.session_state["data"][key] = val
    return val


def persistent_selectbox(
    label: str,
    options: list,
    key: str,
    index: int = 0,
    **kwargs
) -> str:
    """
    Wrapper for st.selectbox that persists value in st.session_state['data'].
    """
    init_session_state()
    
    default_val = options[index] if 0 <= index < len(options) else options[0]
    saved_val = st.session_state["data"].get(key, default_val)
    
    try:
        current_index = options.index(saved_val)
    except ValueError:
        current_index = index
        
    val = st.selectbox(
        label,
        options,
        index=current_index,
        key=key,
        on_change=_on_change_handler,
        args=(key,),
        **kwargs
    )
    
    st.session_state["data"][key] = val
    return val


def persistent_checkbox(
    label: str,
    key: str,
    value: bool = False,
    **kwargs
) -> bool:
    """
    Wrapper for st.checkbox that persists value in st.session_state['data'].
    """
    init_session_state()
    
    current_value = st.session_state["data"].get(key, value)
    
    val = st.checkbox(
        label,
        value=current_value,
        key=key,
        on_change=_on_change_handler,
        args=(key,),
        **kwargs
    )
    
    st.session_state["data"][key] = val
    return val
