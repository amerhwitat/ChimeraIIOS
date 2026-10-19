// Native GTK4 shell for Aurora and Marine desktop personalities.
// This is a Linux/GTK user-space shell client, not a compositor or a Koronos
// syscall port. Koronos GUI readiness remains gated on real process execution,
// graphics/input services, and an OS-native compositor/session implementation.
#include <gtk/gtk.h>
#include <cstring>
#include <string>
#include <vector>
#include <sys/wait.h>

namespace {
const char* desktop_id = "aurora";
bool self_test = false;
GtkLabel* status_label = nullptr;
GtkSearchEntry* app_search_entry = nullptr;
std::vector<GtkWidget*> app_cards;
guint active_children = 0;


const char* desktop_name() {
  return std::strcmp(desktop_id, "marine") == 0
      ? "Marine Desktop" : "Aurora Wayland Glass Desktop";
}

void set_status(const std::string& text) {
  if (status_label) gtk_label_set_text(status_label, text.c_str());
}

void child_exited(GPid pid, gint status, gpointer data) {
  const char* program = static_cast<const char*>(data);
  if (active_children > 0) --active_children;
  std::string message = std::string(program ? program : "Child process") +
      (WIFEXITED(status) ? " exited (code " + std::to_string(WEXITSTATUS(status)) + ")."
                         : WIFSIGNALED(status) ? " terminated by signal " +
                               std::to_string(WTERMSIG(status)) + "."
                                                : " finished.");
  g_spawn_close_pid(pid);
  g_free(data);
  if (status_label) {
    message += " Active child processes: " + std::to_string(active_children) + ".";
    set_status(message);
  }
}

bool spawn_command(const char* program, const char* argument) {
  gchar* path = g_find_program_in_path(program);
  if (!path) return false;
  g_free(path);
  gchar* argv[3] = {const_cast<gchar*>(program),
                    const_cast<gchar*>(argument), nullptr};
  if (!argument) argv[1] = nullptr;
  GError* error = nullptr;
  GPid child_pid = 0;
  const gboolean started = g_spawn_async(
      nullptr, argv, nullptr,
      static_cast<GSpawnFlags>(G_SPAWN_SEARCH_PATH | G_SPAWN_DO_NOT_REAP_CHILD),
      nullptr, nullptr, &child_pid, &error);
  if (!started) {
    set_status(std::string(program) + ": " +
               (error ? error->message : "process launch failed"));
    if (error) g_error_free(error);
  }
  if (started) {
    ++active_children;
    g_child_watch_add(child_pid, child_exited, g_strdup(program));
    set_status(std::string(program) + " started; active child processes: " +
               std::to_string(active_children) + ".");
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

GtkWidget* app_card(const char* glyph, const char* title, const char* detail,
                    const char* action) {
  GtkWidget* card = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
  gtk_widget_add_css_class(card, "app-card");
  const std::string searchable = std::string(title) + " " + detail;
  g_object_set_data_full(G_OBJECT(card), "search-text",
                          g_ascii_strdown(searchable.c_str(), -1), g_free);
  app_cards.push_back(card);
  GtkWidget* icon = gtk_label_new(glyph);
  gtk_widget_add_css_class(icon, "app-glyph");
  GtkWidget* name = gtk_label_new(title);
  gtk_widget_add_css_class(name, "app-name");
  GtkWidget* description = gtk_label_new(detail);
  gtk_label_set_wrap(GTK_LABEL(description), TRUE);
  gtk_widget_add_css_class(description, "app-detail");
  gtk_box_append(GTK_BOX(card), icon);
  gtk_box_append(GTK_BOX(card), name);
  gtk_box_append(GTK_BOX(card), description);
  gtk_box_append(GTK_BOX(card), action_button("Open", action, "accent"));
  return card;
}

void filter_app_cards(GtkSearchEntry* entry, gpointer) {
  const char* raw = gtk_editable_get_text(GTK_EDITABLE(entry));
  gchar* query = g_ascii_strdown(raw ? raw : "", -1);
  for (GtkWidget* card : app_cards) {
    const char* searchable = static_cast<const char*>(
        g_object_get_data(G_OBJECT(card), "search-text"));
    const bool visible = !query || query[0] == 0 ||
        (searchable && g_strstr_len(searchable, -1, query));
    gtk_widget_set_visible(card, visible);
  }
  g_free(query);
}

void nav_clicked(GtkButton*, gpointer data) {
  const char* item = static_cast<const char*>(data);
  if (std::strcmp(item, "Applications") == 0) {
    if (app_search_entry) gtk_widget_grab_focus(GTK_WIDGET(app_search_entry));
    set_status("Search applications by name or description.");
  } else if (std::strcmp(item, "Files") == 0) {
    launch_clicked(nullptr, const_cast<char*>("files"));
  } else if (std::strcmp(item, "Settings") == 0) {
    launch_clicked(nullptr, const_cast<char*>("settings"));
  } else if (std::strcmp(item, "Devices") == 0) {
    set_status("Device controls require installed host service providers.");
  } else if (std::strcmp(item, "Accessibility") == 0) {
    set_status("Host accessibility settings can be opened from Settings; native Aurora accessibility adapters remain in progress.");
  } else {
    set_status("Overview selected.");
  }
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
    .app-card { background: #1b293b; border: 1px solid #31455e; border-radius: 16px; padding: 18px; min-width: 170px; }
    .app-glyph { color: #8fe5ee; font-size: 28px; padding: 8px; }
    .app-name { color: #f4f7ff; font-size: 17px; font-weight: 700; }
    .app-detail { color: #afbdd1; min-height: 48px; }
    button.accent { background: #367c91; color: white; border-radius: 10px; padding: 8px 16px; }
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
    g_signal_connect(nav, "clicked", G_CALLBACK(nav_clicked),
                     const_cast<char*>(item));
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

  app_search_entry = GTK_SEARCH_ENTRY(gtk_search_entry_new());
  gtk_search_entry_set_placeholder_text(app_search_entry,
                                        "Search apps and descriptions…");
  gtk_widget_set_hexpand(GTK_WIDGET(app_search_entry), TRUE);
  g_signal_connect(app_search_entry, "search-changed",
                   G_CALLBACK(filter_app_cards), nullptr);
  gtk_box_append(GTK_BOX(content), GTK_WIDGET(app_search_entry));

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
