import tkinter as tk
from tkinter import ttk

class AutocompleteCombobox(ttk.Combobox):
    """Combobox с автодополнением — работает без зависаний"""
    def __init__(self, master, values=None, **kwargs):
        super().__init__(master, **kwargs)
        self._values = values or []
        self.set('')
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusIn>', self._on_focus)
    
    def _on_focus(self, event):
        self['values'] = self._values
    
    def _on_keyrelease(self, event):
        if event.keysym in ('Down', 'Up', 'Return', 'Escape', 'Tab', 'Shift_L', 'Shift_R', 
                            'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock',
                            'Left', 'Right', 'Home', 'End', 'BackSpace', 'Delete'):
            return
        
        typed = self.get().lower()
        if typed == '':
            self['values'] = self._values
            return
        
        filtered = [item for item in self._values if typed in item.lower()]
        self['values'] = filtered
        if filtered:
            self.event_generate('<Down>')