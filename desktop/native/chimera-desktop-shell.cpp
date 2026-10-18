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
