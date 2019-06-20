# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Credentials view"""

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import messagebox
import urllib
from ._customwidgets import EntryCustom
from ._toolbarview import ToolbarView
from ._dialog import Dialog


class CredentialsView(ttk.Frame):

    def __init__(self, parent, **options):
        super(CredentialsView, self).__init__(parent, **options)

        self.pack(fill=tk.BOTH, expand=tk.TRUE)

        from qiskit.aqua import Preferences
        preferences = Preferences()
        self._cred_prefs = preferences.credentials_preferences

        ttk.Label(self,
                  text="URL:",
                  borderwidth=0,
                  anchor=tk.E).grid(row=0, column=0, pady=5, sticky='nsew')
        urls = [credentials.url for credentials in self._cred_prefs.get_all_credentials()]
        self._url_combobox = URLCombobox(self,
                                         self,
                                         width=80,
                                         exportselection=0,
                                         state='readonly',
                                         values=urls)
        self._url_combobox._text = self._cred_prefs.get_url('')
        self._url_combobox.set(self._url_combobox._text)
        if urls:
            if self._url_combobox.get() in urls:
                self._url_combobox.current(urls.index(self._url_combobox.get()))
            else:
                self._url_combobox.current(0)

        self._url_combobox.grid(row=0, column=1, pady=5, sticky='nsew')

        button_container = tk.Frame(self)
        button_container.grid(row=0, column=2, pady=5, sticky='nsw')
        self._add_button = ttk.Button(button_container,
                                      text='Add',
                                      state='enable',
                                      command=self.cb_add)
        self._remove_button = ttk.Button(button_container,
                                         text='Remove',
                                         state='enable',
                                         command=self.cb_remove)
        self._add_button.pack(side=tk.LEFT)
        if urls:
            self._remove_button.pack(side=tk.LEFT)

        self._api_token = tk.StringVar()
        self._api_token.set(self._cred_prefs.get_token(''))
        ttk.Label(self,
                  text="Token:",
                  borderwidth=0,
                  anchor=tk.E).grid(row=1, column=0, pady=5, sticky='nsew')
        self._api_token_entry = EntryCustom(self,
                                            textvariable=self._api_token,
                                            width=120,
                                            state=tk.NORMAL if urls else tk.DISABLED)
        self._api_token_entry.grid(row=1, column=1, columnspan=2, pady=5, sticky='nsew')

        ttk.Label(self,
                  text="Proxies:",
                  borderwidth=0,
                  anchor=tk.E).grid(row=2, column=0, pady=5, sticky='nsew')
        self._proxiespage = ProxiesPage(self, self._cred_prefs)
        self._proxiespage.grid(row=3, column=0, columnspan=3, pady=5, sticky='nsew')
        self._proxiespage.show_add_button(True)
        self._proxiespage.show_remove_button(self._proxiespage.has_selection())
        self._proxiespage.show_defaults_button(False)
        if not urls:
            self._proxiespage.enable(False)

        self.initial_focus = self._url_combobox

    def cb_add(self):
        urls = [credentials.url for credentials in self._cred_prefs.get_all_credentials()]
        dialog = URLEntryDialog(self.master, self)
        dialog.do_init(tk.LEFT)
        from qiskit.aqua._credentials_preferences import CredentialsPreferences
        if CredentialsPreferences.URL not in urls:
            dialog._url.insert(0, CredentialsPreferences.URL)
        dialog.do_modal()
        if dialog.result is None:
            return

        url = dialog.result
        pref_credentials = self._cred_prefs.get_credentials_with_same_key(url)
        if pref_credentials is not None:
            msg = "URL '{}' will replace current URL '{}'. Continue?".format(url,
                                                                             pref_credentials.url)
            if not messagebox.askyesno('Duplicate Account', msg):
                return

        credentials = self._cred_prefs.set_credentials('', url)
        self._cred_prefs.select_credentials(credentials.url)
        urls = [credentials.url for credentials in self._cred_prefs.get_all_credentials()]
        self._url_combobox.config(values=urls)
        self._url_combobox._text = self._cred_prefs.get_url('')
        self._url_combobox.set(self._url_combobox._text)
        if urls:
            if self._url_combobox.get() in urls:
                self._url_combobox.current(urls.index(self._url_combobox.get()))
            else:
                self._url_combobox.current(0)

            self._remove_button.pack(side=tk.LEFT)
            self._api_token_entry.config(state=tk.NORMAL)
            self._proxiespage.enable(True)

        self._api_token.set(self._cred_prefs.get_token(''))
        self._proxiespage._proxy_urls = self._cred_prefs.get_proxy_urls({})
        self._proxiespage.populate()

    def cb_remove(self):
        self._cred_prefs.remove_credentials(self._url_combobox.get().strip())
        urls = [credentials.url for credentials in self._cred_prefs.get_all_credentials()]
        self._url_combobox.config(values=urls)
        self._url_combobox._text = self._cred_prefs.get_url('')
        self._url_combobox.set(self._url_combobox._text)
        if urls:
            if self._url_combobox.get() in urls:
                self._url_combobox.current(urls.index(self._url_combobox.get()))
            else:
                self._url_combobox.current(0)

        self._api_token.set(self._cred_prefs.get_token(''))
        self._proxiespage._proxy_urls = self._cred_prefs.get_proxy_urls({})
        self._proxiespage.populate()

        if not urls:
            self._remove_button.pack_forget()
            self._api_token_entry.config(state=tk.DISABLED)
            self._proxiespage.enable(False)

    def cb_url_set(self, url):
        # save previously shown data
        if self._cred_prefs.selected_credentials is not None:
            token = self._api_token.get().strip()
            if token == '':
                # go back to previous selection
                urls = [credentials.url
                        for credentials in self._cred_prefs.get_all_credentials()]
                self._url_combobox._text = self._cred_prefs.get_url('')
                self._url_combobox.set(self._url_combobox._text)
                if urls:
                    if self._url_combobox.get() in urls:
                        self._url_combobox.current(urls.index(self._url_combobox.get()))
                    else:
                        self._url_combobox.current(0)

                self._url_combobox.selection_clear()
                self.initial_focus = self._api_token_entry

                def set_focus():
                    self.initial_focus.focus_set()

                self.after(0, set_focus)
                return

            proxy_urls = self._proxiespage._proxy_urls
            if token != self._cred_prefs.get_token('') or \
                    proxy_urls != self._cred_prefs.get_proxy_urls({}):
                self._cred_prefs.set_credentials(token,
                                                 self._cred_prefs.selected_credentials.url,
                                                 proxy_urls)

        self._cred_prefs.select_credentials(url)
        self._api_token.set(self._cred_prefs.get_token(''))
        self._proxiespage._proxy_urls = self._cred_prefs.get_proxy_urls({})
        self._proxiespage.populate()

    def is_valid(self):
        return self._proxiespage.is_valid()

    def validate(self):
        # check current show token
        if self._cred_prefs.selected_credentials is not None:
            token = self._api_token.get().strip()
            if token == '':
                self.initial_focus = self._api_token_entry
                return False

            if not self._proxiespage.is_valid():
                self.initial_focus = self._proxiespage.initial_focus
                return False

        self.initial_focus = self._url_combobox
        return True

    def apply(self, preferences):
        # save previously shown data
        if self._cred_prefs.selected_credentials is not None:
            token = self._api_token.get().strip()
            proxy_urls = self._proxiespage._proxy_urls
            if token != self._cred_prefs.get_token('') or \
                    proxy_urls != self._cred_prefs.get_proxy_urls({}):
                self._cred_prefs.set_credentials(token,
                                                 self._cred_prefs.selected_credentials.url,
                                                 proxy_urls)

        preferences._credentials_preferences = self._cred_prefs

    @staticmethod
    def _is_valid_url(url):
        if url is None or not isinstance(url, str):
            return False

        url = url.strip()
        if not url:
            return False

        min_attributes = ('scheme', 'netloc')
        valid = True
        try:
            token = urllib.parse.urlparse(url)
            if not all([getattr(token, attr) for attr in min_attributes]):
                valid = False
        except Exception:
            valid = False

        return valid

    @staticmethod
    def _validate_url(url):
        valid = CredentialsView._is_valid_url(url)
        if not valid:
            messagebox.showerror("Error", 'Invalid url')

        return valid


class URLCombobox(ttk.Combobox):

    def __init__(self, controller, parent, **options):
        # If relwidth is set, then width is ignored
        super(URLCombobox, self).__init__(parent, **options)
        self._controller = controller
        self.bind("<<ComboboxSelected>>", self._cb_select)
        self._text = None

    def _cb_select(self, *ignore):
        new_text = self.get()
        if new_text and self._text != new_text:
            self._text = new_text
            self._controller.cb_url_set(new_text)


class URLEntryDialog(Dialog):

    def __init__(self, parent, controller):
        super(URLEntryDialog, self).__init__(None, parent, "New URL")
        self._url = None
        self._controller = controller

    def body(self, parent, options):
        ttk.Label(parent,
                  text="URL:",
                  borderwidth=0,
                  anchor=tk.E).grid(padx=7, pady=6, row=0, sticky='nse')
        self._url = EntryCustom(parent, state=tk.NORMAL, width=50)
        self._url.grid(padx=(0, 7), pady=6, row=0, column=1, sticky='nsew')
        return self._url  # initial focus

    def validate(self):
        url = self._url.get().strip()
        if not CredentialsView._validate_url(url):
            self.initial_focus = self._url
            return False

        self.initial_focus = self._url
        return True

    def apply(self):
        self.result = self._url.get().strip()


class ProxiesPage(ToolbarView):

    def __init__(self, parent, preferences, **options):
        super(ProxiesPage, self).__init__(parent, **options)
        size = font.nametofont('TkHeadingFont').actual('size')
        ttk.Style().configure("ProxiesPage.Treeview.Heading", font=(None, size, 'bold'))
        self._tree = ttk.Treeview(
            self, style='ProxiesPage.Treeview', selectmode=tk.BROWSE, height=3, columns=['value'])
        self._tree.heading('#0', text='Protocol')
        self._tree.heading('value', text='URL')
        self._tree.column('#0', minwidth=0, width=150, stretch=tk.NO)
        self._tree.bind('<<TreeviewSelect>>', self._cb_tree_select)
        self._tree.bind('<Button-1>', self._cb_tree_edit)
        self.init_widgets(self._tree)

        self._proxy_urls = preferences.get_proxy_urls({})
        self._popup_widget = None
        self.populate()
        self.initial_focus = self._tree

    def enable(self, enable=True):
        if enable and "disabled" in self._tree.state():
            self._tree.state(("!disabled",))
            self.show_add_button(True)
            self.show_remove_button(self.has_selection())
            return

        if not enable and "disabled" not in self._tree.state():
            self._tree.state(("disabled",))
            self.show_add_button(False)
            self.show_remove_button(False)

    def clear(self):
        if self._popup_widget is not None and self._popup_widget.winfo_exists():
            self._popup_widget.destroy()

        self._popup_widget = None
        for i in self._tree.get_children():
            self._tree.delete([i])

    def populate(self):
        self.clear()
        for protocol, url in self._proxy_urls.items():
            url = '' if url is None else str(url)
            url = url.replace('\r', '\\r').replace('\n', '\\n')
            self._tree.insert('', tk.END, text=protocol, values=[url])

    def set_proxy(self, protocol, url):
        for item in self._tree.get_children():
            if self._tree.item(item, "text") == protocol:
                self._tree.item(item, values=[url])
                break

    def has_selection(self):
        return self._tree.selection()

    def _cb_tree_select(self, event):
        for _ in self._tree.selection():
            self.show_remove_button(True)
            return

    def _cb_tree_edit(self, event):
        if 'disabled' in self._tree.state():
            return

        rowid = self._tree.identify_row(event.y)
        if not rowid:
            return

        column = self._tree.identify_column(event.x)
        if column == '#1':
            x, y, width, height = self._tree.bbox(rowid, column)
            pady = height // 2

            item = self._tree.identify("item", event.x, event.y)
            protocol = self._tree.item(item, "text")
            self._popup_widget = URLPopup(self,
                                          protocol,
                                          self._tree,
                                          self._proxy_urls[protocol],
                                          state=tk.NORMAL)
            self._popup_widget.select_all()
            self._popup_widget.place(x=x, y=y + pady, anchor=tk.W, width=width)

    def cb_add(self):
        dialog = ProxyEntryDialog(self.master, self)
        dialog.do_init(tk.LEFT)
        dialog.do_modal()
        if dialog.result is None:
            return

        if dialog.result is not None:
            self._proxy_urls[dialog.result[0]] = dialog.result[1]
            self.populate()
            self.show_remove_button(self.has_selection())

    def cb_remove(self):
        for item in self._tree.selection():
            protocol = self._tree.item(item, 'text')
            if protocol in self._proxy_urls:
                del self._proxy_urls[protocol]
                self.populate()
                self.show_remove_button(self.has_selection())
            break

    def cb_proxy_set(self, protocol, url):
        protocol = protocol.strip()
        if not protocol:
            return False

        url = url.strip()
        if not CredentialsView._validate_url(url):
            return False

        self._proxy_urls[protocol] = url
        self.populate()
        self.show_remove_button(self.has_selection())
        return True

    def is_valid(self):
        return True

    def validate(self):
        return True

    def apply(self, preferences):
        preferences.set_proxy_urls(self._proxy_urls if self._proxy_urls else None)


class URLPopup(EntryCustom):

    def __init__(self, controller, protocol, parent, url, **options):
        # If relwidth is set, then width is ignored
        super(URLPopup, self).__init__(parent, **options)
        self._controller = controller
        self._protocol = protocol
        self._url = url
        self.insert(0, self._url)
        self.focus_force()
        self.bind("<Unmap>", self._cb_update_value)
        self.bind("<FocusOut>", self._cb_update_value)

    def select_all(self):
        self.focus_force()
        self.selection_range(0, tk.END)

    def _cb_update_value(self, *ignore):
        new_url = self.get().strip()
        valid = True
        if self._url != new_url:
            self._url = new_url
            valid = self._controller.cb_proxy_set(self._protocol, new_url)
        if valid:
            self.destroy()
        else:
            self.select_all()


class ProxyEntryDialog(Dialog):

    def __init__(self, parent, controller):
        super(ProxyEntryDialog, self).__init__(None, parent, "New Proxy")
        self._protocol = None
        self._url = None
        self._controller = controller

    def body(self, parent, options):
        ttk.Label(parent,
                  text="Protocol:",
                  borderwidth=0,
                  anchor=tk.E).grid(padx=7, pady=6, row=0, sticky='nse')
        self._protocol = EntryCustom(parent, state=tk.NORMAL)
        self._protocol.grid(padx=(0, 7), pady=6, row=0, column=1, sticky='nsw')
        ttk.Label(parent,
                  text="URL:",
                  borderwidth=0,
                  anchor=tk.E).grid(padx=7, pady=6, row=1, sticky='nse')
        self._url = EntryCustom(parent, state=tk.NORMAL, width=50)
        self._url.grid(padx=(0, 7), pady=6, row=1, column=1, sticky='nsew')
        return self._protocol  # initial focus

    def validate(self):
        protocol = self._protocol.get().strip()
        if not protocol or protocol in self._controller._proxy_urls:
            self.initial_focus = self._protocol
            return False

        url = self._url.get().strip()
        if not CredentialsView._validate_url(url):
            self.initial_focus = self._url
            return False

        self.initial_focus = self._protocol
        return True

    def apply(self):
        self.result = (self._protocol.get().strip(), self._url.get().strip())
