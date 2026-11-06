// Native GTK4 shell for Aurora and Marine desktop personalities.
// This is a Linux/GTK user-space shell client, not a compositor or a Koronos
// syscall port. Koronos GUI readiness remains gated on real process execution,
// graphics/input services, and an OS-native compositor/session implementation.
#include <gtk/gtk.h>
#include <cstring>
#include <string>

namespace {
const char* desktop_id = "aurora";
bool self_test = false;
GtkLabel* status_label = nullptr;
GtkWidget* selected_app_card = nullptr;

struct AppCardInfo {
  std::string title;
  std::string detail;
  const char* action;
  GtkLabel* title_label;
};

const char* desktop_name() {
  return std::strcmp(desktop_id, "marine") == 0
      ? "Marine Desktop" : "Aurora Wayland Glass Desktop";
}

void set_status(const std::string& text) {
  if (status_label) gtk_label_set_text(status_label, text.c_str());
}

bool spawn_command(const char* program, const char* argument) {
  gchar* path = g_find_program_in_path(program);
  if (!path) return false;
  g_free(path);
  gchar* argv[3] = {const_cast<gchar*>(program),
                    const_cast<gchar*>(argument), nullptr};
  if (!argument) argv[1] = nullptr;
  GError* error = nullptr;
  const gboolean started = g_spawn_async(
      nullptr, argv, nullptr,
      G_SPAWN_SEARCH_PATH,
      nullptr, nullptr, nullptr, &error);
  if (!started) {
    set_status(std::string(program) + ": " +
               (error ? error->message : "process launch failed"));
    if (error) g_error_free(error);
  }
  return started;
}

void launch_clicked(GtkButton*, gpointer data) {
  const char* action = static_cast<const char*>(data);
  if (std::strcmp(action, "terminal") == 0) {
    const char* candidates[] = {"x-terminal-emulator", "kgx", "gnome-terminal",
                                "konsole", "xfce4-terminal", nullptr};
    for (size_t i = 0; candidates[i]; ++i) {
      if (spawn_command(candidates[i], nullptr)) {
        set_status("Terminal launched through the host desktop.");
        return;
      }
    }
  } else if (std::strcmp(action, "files") == 0) {
    if (spawn_command("xdg-open", g_get_home_dir())) {
      set_status("Home folder opened through the host file handler.");
      return;
    }
  } else if (std::strcmp(action, "browser") == 0) {
    if (spawn_command("xdg-open", "https://www.example.com")) {
      set_status("Browser request delegated to the host URL handler.");
      return;
    }
  } else if (std::strcmp(action, "settings") == 0) {
    if (spawn_command("gnome-control-center", nullptr)) {
      set_status("Host settings opened.");
      return;
    }
  } else if (std::strcmp(action, "voiceconnect") == 0) {
    if (spawn_command("/usr/share/chimera/aurora/voiceconnect-launcher.sh", nullptr) ||
        spawn_command("xdg-open", "https://github.com/amerhwitat/test/tree/feat/voiceconnect-p2p-camera")) {
      set_status("VoiceConnect launch requested; installed-package status is handled by its launcher.");
      return;
    }
  }
  set_status(std::string(action) +
             ": no supported host application is installed.");
}

GtkWidget* action_button(const char* label, const char* action,
                         const char* css_class) {
  GtkWidget* button = gtk_button_new_with_label(label);
  gtk_widget_add_css_class(button, css_class);
  g_signal_connect(button, "clicked", G_CALLBACK(launch_clicked),
                   const_cast<char*>(action));
  return button;
}


AppCardInfo* card_info(GtkWidget* card) {
  return static_cast<AppCardInfo*>(g_object_get_data(G_OBJECT(card), "chimera-app-card-info"));
}

void show_app_properties(GtkWidget* card) {
  AppCardInfo* info = card_info(card);
  if (!info) return;
  GtkRoot* root = gtk_widget_get_root(card);
  GtkWindow* parent = root && GTK_IS_WINDOW(root) ? GTK_WINDOW(root) : nullptr;
  GtkWidget* dialog = gtk_message_dialog_new(
      parent, GTK_DIALOG_MODAL, GTK_MESSAGE_INFO, GTK_BUTTONS_CLOSE,
      "%s", info->title.c_str());
  gtk_message_dialog_format_secondary_text(
      GTK_MESSAGE_DIALOG(dialog), "%s\nAction: %s\n%s",
      info->detail.c_str(), info->action,
      "Shortcut properties describe this shell card; they are not filesystem metadata.");
  g_signal_connect_swapped(dialog, "response", G_CALLBACK(gtk_window_destroy), dialog);
  gtk_window_present(GTK_WINDOW(dialog));
}

void rename_response(GtkDialog* dialog, int response, gpointer) {
  GtkWidget* card = GTK_WIDGET(g_object_get_data(G_OBJECT(dialog), "chimera-card"));
  GtkWidget* entry = GTK_WIDGET(g_object_get_data(G_OBJECT(dialog), "chimera-rename-entry"));
  AppCardInfo* info = card ? card_info(card) : nullptr;
  if (response == GTK_RESPONSE_ACCEPT && info && entry) {
    const char* value = gtk_editable_get_text(GTK_EDITABLE(entry));
    if (value && value[0]) {
      info->title = value;
      gtk_label_set_text(info->title_label, info->title.c_str());
      set_status("Shortcut label renamed in this desktop session.");
    }
  }
  gtk_window_destroy(GTK_WINDOW(dialog));
}

void rename_app_card(GtkWidget* card) {
  AppCardInfo* info = card_info(card);
  if (!info) return;
  GtkRoot* root = gtk_widget_get_root(card);
  GtkWindow* parent = root && GTK_IS_WINDOW(root) ? GTK_WINDOW(root) : nullptr;
  GtkWidget* dialog = gtk_dialog_new_with_buttons(
      "Rename shortcut", parent, GTK_DIALOG_MODAL,
      "_Cancel", GTK_RESPONSE_CANCEL, "_Rename", GTK_RESPONSE_ACCEPT, nullptr);
  GtkWidget* entry = gtk_entry_new();
  gtk_editable_set_text(GTK_EDITABLE(entry), info->title.c_str());
  gtk_widget_set_margin_top(entry, 12);
  gtk_widget_set_margin_bottom(entry, 12);
  gtk_widget_set_margin_start(entry, 12);
  gtk_widget_set_margin_end(entry, 12);
  gtk_box_append(GTK_BOX(gtk_dialog_get_content_area(GTK_DIALOG(dialog))), entry);
  g_object_set_data(G_OBJECT(dialog), "chimera-card", card);
  g_object_set_data(G_OBJECT(dialog), "chimera-rename-entry", entry);
  g_signal_connect(dialog, "response", G_CALLBACK(rename_response), nullptr);
  gtk_window_present(GTK_WINDOW(dialog));
  gtk_widget_grab_focus(entry);
  gtk_editable_select_region(GTK_EDITABLE(entry), 0, -1);
}

void close_card_context(GtkButton* button) {
  GtkWidget* popover = gtk_widget_get_ancestor(GTK_WIDGET(button), GTK_TYPE_POPOVER);
  if (popover) gtk_popover_popdown(GTK_POPOVER(popover));
}
void context_open_clicked(GtkButton* button, gpointer data) {
  close_card_context(button);
  GtkWidget* card = GTK_WIDGET(data);
  AppCardInfo* info = card_info(card);
  if (info) launch_clicked(nullptr, const_cast<char*>(info->action));
}
void context_properties_clicked(GtkButton* button, gpointer data) {
  close_card_context(button);
  show_app_properties(GTK_WIDGET(data));
}
void context_rename_clicked(GtkButton* button, gpointer data) {
  close_card_context(button);
  rename_app_card(GTK_WIDGET(data));
}
void context_popover_closed(GtkPopover* popover, gpointer) {
  gtk_widget_unparent(GTK_WIDGET(popover));
}
void show_app_context_menu(GtkWidget* card, double x, double y) {
  GtkWidget* popover = gtk_popover_new();
  GtkWidget* actions = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
  gtk_widget_add_css_class(actions, "context-actions");
  gtk_popover_set_child(GTK_POPOVER(popover), actions);
  gtk_widget_set_parent(popover, card);
  const struct { const char* label; GCallback callback; } entries[] = {
      {"Open", G_CALLBACK(context_open_clicked)},
      {"Rename", G_CALLBACK(context_rename_clicked)},
      {"Properties", G_CALLBACK(context_properties_clicked)}
  };
  for (const auto& entry : entries) {
    GtkWidget* button = gtk_button_new_with_label(entry.label);
    gtk_widget_add_css_class(button, "context-action");
    g_signal_connect(button, "clicked", entry.callback, card);
    gtk_box_append(GTK_BOX(actions), button);
  }
  GdkRectangle rect{static_cast<int>(x), static_cast<int>(y), 1, 1};
  gtk_popover_set_pointing_to(GTK_POPOVER(popover), &rect);
  g_signal_connect(popover, "closed", G_CALLBACK(context_popover_closed), nullptr);
  gtk_popover_popup(GTK_POPOVER(popover));
}
void card_pointer_pressed(GtkGestureClick* gesture, int n_press,
                          double x, double y, gpointer data) {
  GtkWidget* card = GTK_WIDGET(data);
  selected_app_card = card;
  if (gtk_gesture_single_get_current_button(GTK_GESTURE_SINGLE(gesture)) == GDK_BUTTON_SECONDARY) {
    show_app_context_menu(card, x, y);
    return;
  }
  if (n_press == 2) {
    AppCardInfo* info = card_info(card);
    if (info) launch_clicked(nullptr, const_cast<char*>(info->action));
  }
}
gboolean shell_key_pressed(GtkEventControllerKey*, guint keyval, guint,
                           GdkModifierType state, gpointer) {
  if (keyval == GDK_KEY_F2 && selected_app_card) {
    rename_app_card(selected_app_card);
    return TRUE;
  }
  if (keyval == GDK_KEY_Return && selected_app_card) {
    AppCardInfo* info = card_info(selected_app_card);
    if (info) launch_clicked(nullptr, const_cast<char*>(info->action));
    return TRUE;
  }
  if (keyval == GDK_KEY_F10 && (state & GDK_SHIFT_MASK) && selected_app_card) {
    show_app_context_menu(selected_app_card, 16, 16);
    return TRUE;
  }
  if ((state & (GDK_CONTROL_MASK | GDK_ALT_MASK)) ==
      (GDK_CONTROL_MASK | GDK_ALT_MASK) && keyval == GDK_KEY_t) {
    launch_clicked(nullptr, const_cast<char*>("terminal"));
    return TRUE;
  }
  if ((state & (GDK_SUPER_MASK | GDK_META_MASK)) && keyval == GDK_KEY_e) {
    launch_clicked(nullptr, const_cast<char*>("files"));
    return TRUE;
  }
  if (keyval == GDK_KEY_Escape) {
    set_status("Dismissed desktop popup.");
    return FALSE;
  }
  return FALSE;
}

GtkWidget* app_card(const char* glyph, const char* title, const char* detail,
                    const char* action) {
  GtkWidget* card = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
  gtk_widget_add_css_class(card, "app-card");
  GtkWidget* icon = gtk_label_new(glyph);
  gtk_widget_add_css_class(icon, "app-glyph");
  GtkWidget* name = gtk_label_new(title);
  gtk_widget_add_css_class(name, "app-name");
  GtkWidget* description = gtk_label_new(detail);
  gtk_label_set_wrap(GTK_LABEL(description), TRUE);
  gtk_widget_add_css_class(description, "app-detail");
  auto* info = new AppCardInfo{title, detail, action, GTK_LABEL(name)};
  g_object_set_data_full(G_OBJECT(card), "chimera-app-card-info", info,
      [](gpointer value) { delete static_cast<AppCardInfo*>(value); });
  gtk_box_append(GTK_BOX(card), icon);
  gtk_box_append(GTK_BOX(card), name);
  gtk_box_append(GTK_BOX(card), description);
  gtk_box_append(GTK_BOX(card), action_button("Open", action, "accent"));
  GtkGesture* pointer = gtk_gesture_click_new();
  gtk_gesture_single_set_button(GTK_GESTURE_SINGLE(pointer), 0);
  g_signal_connect(pointer, "pressed", G_CALLBACK(card_pointer_pressed), card);
  gtk_widget_add_controller(card, GTK_EVENT_CONTROLLER(pointer));
  return card;
}


void desktop_menu_action(GtkButton* button, gpointer data) {
  const char* action = static_cast<const char*>(data);
  GtkWidget* popover = gtk_widget_get_ancestor(GTK_WIDGET(button), GTK_TYPE_POPOVER);
  if (popover) gtk_popover_popdown(GTK_POPOVER(popover));
  if (std::strcmp(action, "files") == 0) {
    launch_clicked(nullptr, const_cast<char*>("files"));
  } else if (std::strcmp(action, "terminal") == 0) {
    launch_clicked(nullptr, const_cast<char*>("terminal"));
  } else if (std::strcmp(action, "rename") == 0) {
    if (selected_app_card) rename_app_card(selected_app_card);
    else set_status("Select an application shortcut before renaming.");
  } else if (std::strcmp(action, "properties") == 0) {
    if (selected_app_card) show_app_properties(selected_app_card);
    else set_status("Select an application shortcut to view Properties.");
  } else if (std::strcmp(action, "refresh") == 0) {
    GtkRoot* root = gtk_widget_get_root(GTK_WIDGET(button));
    if (root) gtk_widget_queue_draw(GTK_WIDGET(root));
    set_status("Desktop view refreshed.");
  } else if (std::strcmp(action, "backgrounds") == 0) {
    set_status("Background selection requires the native compositor wallpaper provider.");
  } else if (std::strcmp(action, "apps") == 0) {
    set_status("Applications workspace is shown below.");
  } else if (std::strcmp(action, "showdesktop") == 0) {
    selected_app_card = nullptr;
    set_status("Desktop overview selected.");
  } else if (std::strcmp(action, "shortcuts") == 0) {
    set_status("Shortcuts: F2 rename · Enter open · Shift+F10 context menu · Ctrl+Alt+T Terminal · Super/Meta+E Files.");
  } else if (std::strcmp(action, "about") == 0) {
    set_status("Chimera II Aurora/Marine GTK4 shell. Koronos native userspace readiness is a separate release gate.");
  } else if (std::strcmp(action, "quit") == 0) {
    GtkRoot* root = gtk_widget_get_root(GTK_WIDGET(button));
    if (root && GTK_IS_WINDOW(root)) gtk_window_close(GTK_WINDOW(root));
  }
}

GtkWidget* desktop_menu_button(const char* title,
                               const char* const* labels,
                               const char* const* actions,
                               int count) {
  GtkWidget* menu_button = gtk_menu_button_new();
  gtk_menu_button_set_label(GTK_MENU_BUTTON(menu_button), title);
  gtk_widget_add_css_class(menu_button, "desktop-menu-button");
  GtkWidget* popover = gtk_popover_new();
  GtkWidget* box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
  gtk_widget_add_css_class(box, "desktop-menu-actions");
  for (int i = 0; i < count; ++i) {
    GtkWidget* item = gtk_button_new_with_label(labels[i]);
    gtk_widget_add_css_class(item, "context-action");
    g_signal_connect(item, "clicked", G_CALLBACK(desktop_menu_action),
                     const_cast<char*>(actions[i]));
    gtk_box_append(GTK_BOX(box), item);
  }
  gtk_popover_set_child(GTK_POPOVER(popover), box);
  gtk_menu_button_set_popover(GTK_MENU_BUTTON(menu_button), popover);
  return menu_button;
}

GtkWidget* desktop_menu_bar() {
  GtkWidget* bar = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
  gtk_widget_add_css_class(bar, "desktop-menubar");
  const char* file_labels[] = {"Open Files", "Open Terminal", "Quit"};
  const char* file_actions[] = {"files", "terminal", "quit"};
  const char* edit_labels[] = {"Rename Selected", "Properties"};
  const char* edit_actions[] = {"rename", "properties"};
  const char* view_labels[] = {"Refresh Desktop", "Backgrounds"};
  const char* view_actions[] = {"refresh", "backgrounds"};
  const char* window_labels[] = {"Applications", "Show Desktop"};
  const char* window_actions[] = {"apps", "showdesktop"};
  const char* help_labels[] = {"Keyboard Shortcuts", "About"};
  const char* help_actions[] = {"shortcuts", "about"};
  gtk_box_append(GTK_BOX(bar), desktop_menu_button("File", file_labels, file_actions, 3));
  gtk_box_append(GTK_BOX(bar), desktop_menu_button("Edit", edit_labels, edit_actions, 2));
  gtk_box_append(GTK_BOX(bar), desktop_menu_button("View", view_labels, view_actions, 2));
  gtk_box_append(GTK_BOX(bar), desktop_menu_button("Window", window_labels, window_actions, 2));
  gtk_box_append(GTK_BOX(bar), desktop_menu_button("Help", help_labels, help_actions, 2));
  return bar;
}

void install_style() {
  const char* css = R"CSS(
    window { background: #101723; color: #eef4ff; }
    headerbar { background: #172234; color: #f4f7ff; border: 0; min-height: 48px; }
    .sidebar { background: #121d2c; padding: 22px 14px; }
    .brand { color: #8fe5ee; font-weight: 800; padding: 8px 0 22px; }
    .nav-button { background: transparent; color: #d8e2f2; border: 0; border-radius: 10px; padding: 10px; }
    .nav-button:hover { background: #263850; }
    .hero { color: #f2f7ff; font-size: 28px; font-weight: 800; }
    .muted { color: #9fb0c8; }
    .app-card { background: linear-gradient(155deg,#263c56,#18283b 58%,#101b2a); border: 1px solid #526a86; border-radius: 16px; padding: 18px; min-width: 170px; box-shadow: 0 6px 0 #07101b,0 15px 28px #0008; }
    .app-card:hover { border-color: #8fe5ee; }
    .context-actions { background: #17283c; padding: 7px; border: 1px solid #68839d; border-radius: 12px; }
    .desktop-menubar { background: #152338; padding: 6px 12px; border-bottom: 1px solid #344d68; }
    .desktop-menu-button { background: transparent; color: #eaf4ff; border: 1px solid transparent; border-radius: 8px; padding: 6px 12px; }
    .desktop-menu-button:hover { background: #2a405b; border-color: #54728e; }
    button.context-action { background: #243b54; color: #f4f8ff; border: 1px solid #49637d; border-radius: 8px; padding: 8px 14px; }
    button.context-action:hover { background: #315675; }
    .app-glyph { color: #8fe5ee; font-size: 28px; padding: 8px; }
    .app-name { color: #f4f7ff; font-size: 17px; font-weight: 700; }
    .app-detail { color: #afbdd1; min-height: 48px; }
    button.accent { background: linear-gradient(160deg,#56a8bb,#28657d 65%,#19445b); color: white; border-radius: 10px; padding: 8px 16px; box-shadow: 0 4px 0 #102c3b,0 8px 16px #0005; transition: transform .12s ease,box-shadow .12s ease,filter .12s ease; }
    button.accent:active { transform: translateY(2px); box-shadow: 0 1px 0 #102c3b,0 3px 7px #0005; }
    button.accent:hover { background: #459bb1; }
    .footer { background: #121d2c; padding: 12px 24px; }
    .window-title { font-weight: 700; }
    window.marine { background: #111827; }
    window.marine headerbar { background: #1d293b; }
    window.marine .sidebar { background: #182337; }
    window.marine .brand { color: #91b9ff; }
    window.marine button.accent { background: #2563eb; }
  )CSS";
  GdkDisplay* display = gdk_display_get_default();
  if (!display) return;
  GtkCssProvider* provider = gtk_css_provider_new();
  gtk_css_provider_load_from_data(provider, css, -1);
  gtk_style_context_add_provider_for_display(
      display, GTK_STYLE_PROVIDER(provider), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
  g_object_unref(provider);
}

void activate(GtkApplication* app, gpointer) {
  install_style();
  GtkWidget* window = gtk_application_window_new(app);
  gtk_window_set_title(GTK_WINDOW(window), desktop_name());
  gtk_window_set_default_size(GTK_WINDOW(window), 1280, 800);
  GtkEventController* key_controller = gtk_event_controller_key_new();
  g_signal_connect(key_controller, "key-pressed", G_CALLBACK(shell_key_pressed), nullptr);
  gtk_widget_add_controller(window, key_controller);
  gtk_widget_add_css_class(window, std::strcmp(desktop_id, "marine") == 0
                                      ? "marine" : "aurora");

  GtkWidget* root = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  gtk_window_set_child(GTK_WINDOW(window), root);
  GtkWidget* header = gtk_header_bar_new();
  GtkWidget* title = gtk_label_new(desktop_name());
  gtk_widget_add_css_class(title, "window-title");
  gtk_header_bar_set_title_widget(GTK_HEADER_BAR(header), title);
  gtk_header_bar_set_show_title_buttons(GTK_HEADER_BAR(header), TRUE);
  gtk_box_append(GTK_BOX(root), header);
  gtk_box_append(GTK_BOX(root), desktop_menu_bar());

  GtkWidget* body = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
  gtk_widget_set_vexpand(body, TRUE);
  gtk_box_append(GTK_BOX(root), body);
  GtkWidget* sidebar = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
  gtk_widget_add_css_class(sidebar, "sidebar");
  gtk_widget_set_size_request(sidebar, 220, -1);
  gtk_box_append(GTK_BOX(body), sidebar);
  GtkWidget* brand = gtk_label_new(std::strcmp(desktop_id, "marine") == 0
                                       ? "MARINE  •  WORKSPACE"
                                       : "AURORA  •  WORKSPACE");
  gtk_widget_add_css_class(brand, "brand");
  gtk_box_append(GTK_BOX(sidebar), brand);
  for (const char* item : {"Overview", "Applications", "Files", "Settings",
                           "Devices", "Accessibility"}) {
    GtkWidget* nav = gtk_button_new_with_label(item);
    gtk_widget_add_css_class(nav, "nav-button");
    gtk_box_append(GTK_BOX(sidebar), nav);
  }
  GtkWidget* spacer = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  gtk_widget_set_vexpand(spacer, TRUE);
  gtk_box_append(GTK_BOX(sidebar), spacer);
  GtkWidget* side_status = gtk_label_new("Native shell session");
  gtk_widget_add_css_class(side_status, "muted");
  gtk_box_append(GTK_BOX(sidebar), side_status);

  GtkWidget* content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 18);
  gtk_widget_set_hexpand(content, TRUE);
  gtk_widget_set_margin_top(content, 28);
  gtk_widget_set_margin_bottom(content, 24);
  gtk_widget_set_margin_start(content, 30);
  gtk_widget_set_margin_end(content, 30);
  gtk_box_append(GTK_BOX(body), content);
  GtkWidget* heading = gtk_label_new(std::strcmp(desktop_id, "marine") == 0
                                         ? "Your workspace, at a glance"
                                         : "A calmer place to work");
  gtk_widget_set_halign(heading, GTK_ALIGN_START);
  gtk_widget_add_css_class(heading, "hero");
  gtk_box_append(GTK_BOX(content), heading);
  GtkWidget* subtitle = gtk_label_new(
      "Native GTK4 shell • launches delegate to installed host services");
  gtk_widget_set_halign(subtitle, GTK_ALIGN_START);
  gtk_widget_add_css_class(subtitle, "muted");
  gtk_box_append(GTK_BOX(content), subtitle);

  GtkWidget* grid = gtk_grid_new();
  gtk_grid_set_row_spacing(GTK_GRID(grid), 16);
  gtk_grid_set_column_spacing(GTK_GRID(grid), 16);
  gtk_widget_set_vexpand(grid, TRUE);
  gtk_box_append(GTK_BOX(content), grid);
  gtk_grid_attach(GTK_GRID(grid), app_card("⌘", "Terminal",
      "Run commands using an installed terminal emulator.", "terminal"), 0, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("▣", "Files",
      "Open your home folder with the host file handler.", "files"), 1, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("◎", "Web",
      "Open a URL using the configured browser handler.", "browser"), 2, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("⚙", "Settings",
      "Open host settings when the provider is installed.", "settings"), 0, 1, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("🎙", "VoiceConnect",
      "Launch an installed optional package or open its upstream project page.", "voiceconnect"), 1, 1, 1, 1);

  GtkWidget* footer = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
  gtk_widget_add_css_class(footer, "footer");
  status_label = GTK_LABEL(gtk_label_new(
      "Ready. This GTK shell is not evidence of Koronos USERSPACE READY."));
  gtk_label_set_xalign(status_label, 0.0f);
  gtk_label_set_wrap(status_label, TRUE);
  gtk_box_append(GTK_BOX(footer), GTK_WIDGET(status_label));
  gtk_box_append(GTK_BOX(root), footer);
  gtk_window_present(GTK_WINDOW(window));
  if (self_test) g_idle_add([](gpointer data) -> gboolean {
    g_application_quit(G_APPLICATION(data));
    return G_SOURCE_REMOVE;
  }, app);
}
}  // namespace

int main(int argc, char** argv) {
  for (int i = 1; i < argc; ++i) {
    if (std::strncmp(argv[i], "--desktop=", 10) == 0) {
      const char* value = argv[i] + 10;
      if (std::strcmp(value, "aurora") == 0 || std::strcmp(value, "marine") == 0)
        desktop_id = value;
      else {
        g_printerr("Unknown desktop '%s'; use aurora or marine.\n", value);
        return 2;
      }
    } else if (std::strcmp(argv[i], "--self-test") == 0) {
      self_test = true;
    } else {
      g_printerr("Usage: %s [--desktop=aurora|marine] [--self-test]\n", argv[0]);
      return 2;
    }
  }
  GtkApplication* app = gtk_application_new(
      "org.chimera.desktop.shell", G_APPLICATION_NON_UNIQUE);
  g_signal_connect(app, "activate", G_CALLBACK(activate), nullptr);
  char* app_argv[] = {argv[0], nullptr};
  const int result = g_application_run(G_APPLICATION(app), 1, app_argv);
  g_object_unref(app);
  return result;
}
