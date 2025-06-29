import flet as ft
from functools import partial

chat_users = ["Alice", "Bob", "Charlie", "Dave"]
chat_messages = {
    "Alice": ["Hi there!", "How are you?"],
    "Bob": ["Hey!", "Let's meet at 3 PM."],
    "Charlie": ["Check this out!", "👍"],
    "Dave": ["Hello!", "Long time no see."]
}

user_avatars = {
    "Alice": "A",
    "Bob": "B",
    "Charlie": "C",
    "Dave": "D"
}
current_theme = {"value": "light"}
current_chat = {"user": None}
current_input = {"field": None}

def get_colors(theme):
    if theme == "light":
        return dict(
            left_bg=ft.Colors.BLUE_GREY_200,
            chat_bg=ft.Colors.BLUE_GREY_50,
            msg_bg=ft.Colors.BLACK12,
            my_msg_bg=ft.Colors.BLUE_100,
            text_color=ft.Colors.BLACK,
            input_bg_color=ft.Colors.WHITE70,
        )
    else:
        return dict(
            left_bg=ft.Colors.BLACK12,
            chat_bg=ft.Colors.BLACK,
            msg_bg=ft.Colors.WHITE10,
            my_msg_bg=ft.Colors.BLUE_GREY_700,
            text_color=ft.Colors.WHITE,
            input_bg_color=ft.Colors.WHITE12,
        )


def main(page: ft.Page):
   
    
    colors = get_colors(current_theme["value"])
    
    message_column = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=10,
        auto_scroll=True
    )
    
    def send_message(e):
        user = current_chat["user"]
        text = current_input["field"].value.strip()
        if user and text:
            chat_messages.setdefault(user, []).append(text)
            message_column.controls.append(
                ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Text("You"), radius=15),
                        ft.Container(
                            content=ft.Text(text, color=colors["text_color"]),
                            bgcolor=colors["my_msg_bg"],
                            padding=10,
                            border_radius=5
                        )
                    ],
                    spacing=10
                )
            )
            current_input["field"].value = ""
            current_input["field"].focus()
            page.update()
    
    def build_input_row():
        input_field = ft.TextField(
            hint_text="Type a message...",
            expand=True,
            autofocus=True,
            on_submit=send_message,
            bgcolor=colors["input_bg_color"],
            color=colors["text_color"]
        )
        current_input["field"] = input_field
        return ft.Row([input_field])
    
    def build_user_list():
        user_list = ft.ListView(expand=True)
        for user in chat_users:
            user_item = ft.ListTile(
                leading=ft.CircleAvatar(
                    content=ft.Text(user_avatars.get(user, "?")),
                    radius=15
                ),
                title=ft.Text(user, color=colors["text_color"]),
                on_click=partial(load_chat, user),
            )
            user_list.controls.append(user_item)
        return user_list
    
    def load_chat(name, e):
        current_chat["user"] = name
        message_column.controls.clear()
        for msg in chat_messages.get(name, []):
            message_column.controls.append(
                ft.Row(
                    [
                        ft.CircleAvatar(content=ft.Text(user_avatars.get(name, "?")), radius=15),
                        ft.Container(
                            content=ft.Text(msg, selectable=True, color=colors["text_color"]),
                            bgcolor=colors["msg_bg"],
                            padding=10,
                            border_radius=5
                        )
                    ],
                    spacing=10
                )
            )
        page.update()
    
    def build_chat_ui():
        user_list = build_user_list()
        input_row = build_input_row()
        settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="Settings",
            on_click=open_settings
        )
        
        layout = ft.Column([
            ft.Row([settings_button]),
            ft.Row(
                [
                    ft.Container(content=user_list, width=200, bgcolor=colors["left_bg"]),
                    ft.Container(
                        content=ft.Column([message_column, input_row], expand=True),
                        bgcolor=colors["chat_bg"],
                        expand=True,
                        padding=20
                    )
                ],
                expand=True
            )
        ], expand=True)
        return layout
    
    def build_settings_ui():
        theme_toggle = ft.Switch(
            value=(current_theme["value"] == "dark"),
            on_change=toggle_theme,
        )
        label = ft.Text(
            "Theme",
            size=15,
            color=colors["text_color"]
        )
        back_button = ft.ElevatedButton(
            text="Back to Chat",
            on_click=back_to_chat
        )
        
        toggle_row = ft.Row(
            [theme_toggle, label],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        settings_content = ft.Column(
            [
                ft.Text("Settings", size=30, color=colors["text_color"]),
                toggle_row,
                back_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30
        )
        
        return ft.Container(
            content=settings_content,
            bgcolor=colors["chat_bg"],
            expand=True,
            alignment=ft.alignment.center,
            padding=40
        )
    
    def toggle_theme(e):
        if e.control.value:
            current_theme["value"] = "dark"
        else:
            current_theme["value"] = "light"
        new_colors = get_colors(current_theme["value"])
        colors.update(new_colors)
        open_settings()
    
    def open_settings(_=None):
        page.controls.clear()
        page.add(build_settings_ui())
    
    def back_to_chat(_=None):
        page.controls.clear()
        page.add(build_chat_ui())
        if current_chat["user"]:
            load_chat(current_chat["user"], None)
    
    page.add(build_chat_ui())


ft.app(target=main)
