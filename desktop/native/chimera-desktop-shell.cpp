// Native GTK4 shell for Aurora, Marine and FreeXP desktop personalities.
// This is a Linux/GTK user-space shell client, not a compositor or a Koronos
// syscall port. Koronos GUI readiness remains gated on real process execution,
// graphics/input services, and an OS-native compositor/session implementation.
#include <gtk/gtk.h>
#include <cstring>
#include <string>

namespace {
const char* desktop_id = "aurora";
bool self_test = false;
int semantic_icon_failures = 0;
GtkLabel* status_label = nullptr;

const char* desktop_name() {
  if (std::strcmp(desktop_id, "marine") == 0) return "Marine Blue Desktop";
  if (std::strcmp(desktop_id, "freexp") == 0) return "FreeXP Classic Desktop";
  if (std::strcmp(desktop_id, "freewin11") == 0) return "FreeWin11 Desktop";
  return "Aurora Wayland Glass Desktop";
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
  } else if (std::strcmp(action, "dos") == 0) {
    const char* candidates[] = {"dosbox-x", "dosbox", nullptr};
    for (size_t i = 0; candidates[i]; ++i) {
      if (spawn_command(candidates[i], nullptr)) {
        set_status(std::string(candidates[i]) + " launched for DOS applications.");
        return;
      }
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
                    const char* action, const char* semantic_icon) {
  GtkWidget* card = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
  gtk_widget_add_css_class(card, "app-card");
  const char* icon_dir = g_getenv("CHIMERA_ICON_DIR");
  if (!icon_dir || !*icon_dir) icon_dir = "desktop/aurora/icons/generated";
  gchar* icon_path = g_build_filename(icon_dir,
      (std::string(semantic_icon) + ".svg").c_str(), nullptr);
  GtkWidget* icon = nullptr;
  if (g_file_test(icon_path, G_FILE_TEST_IS_REGULAR)) {
    icon = gtk_image_new_from_file(icon_path);
    gtk_image_set_pixel_size(GTK_IMAGE(icon), 64);
    if (gtk_image_get_storage_type(GTK_IMAGE(icon)) == GTK_IMAGE_EMPTY) {
      ++semantic_icon_failures;
      gtk_widget_set_tooltip_text(icon, "Failed to load semantic SVG icon");
    } else {
      gtk_widget_set_tooltip_text(icon, semantic_icon);
    }
  } else {
    ++semantic_icon_failures;
    icon = gtk_label_new(glyph);
    gtk_widget_set_tooltip_text(icon, "Semantic icon unavailable; text fallback");
  }
  g_free(icon_path);
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
    window.freexp { background: #c9dcf4; color: #15385f; }
    window.freexp headerbar { background: linear-gradient(to bottom, #5c96e6, #174b91); color: white; border-bottom: 2px solid #10376d; }
    window.freexp .sidebar { background: linear-gradient(to bottom, #dceafb, #a6c5eb); }
    window.freexp .brand { color: #123f7a; }
    window.freexp .nav-button { background: #edf5ff; color: #17477f; border: 1px solid #8eadd4; border-radius: 6px; }
    window.freexp .nav-button:hover { background: #ffffff; }
    window.freexp .hero { color: #103d78; }
    window.freexp .muted { color: #315a86; }
    window.freexp .app-card { background: linear-gradient(to bottom, #ffffff, #e6f0ff); border: 1px solid #82a8d5; border-radius: 9px; padding: 18px; }
    window.freexp .app-glyph { color: #1c5ba7; }
    window.freexp .app-name { color: #123d72; }
    window.freexp .app-detail { color: #315a86; }
    window.freexp button.accent { background: linear-gradient(to bottom, #77aaf3, #2d65b2); color: white; border: 1px solid #17488b; border-radius: 6px; }
    window.freexp .footer { background: #d9e8f9; color: #153e70; border-top: 1px solid #8aaed8; }
    window.freexp .freexp-taskbar { background: linear-gradient(to bottom, #3d7ed2, #174a92); padding: 7px 12px; border-top: 1px solid #9bbdf0; }
    window.freexp .freexp-start { background: linear-gradient(to bottom, #7bd45d, #238b27); color: white; border: 1px solid #1d6e20; border-radius: 12px 6px 6px 12px; padding: 6px 18px; font-weight: 800; }
    window.freexp .freexp-quick { background: rgba(255,255,255,0.16); color: white; border: 1px solid rgba(255,255,255,0.35); border-radius: 6px; padding: 6px 12px; }
    window.freexp .freexp-start-menu { background: #e8f1ff; border: 1px solid #285d9c; padding: 12px; }
    window.freexp .freexp-menu-title { color: #153e72; font-weight: 800; padding: 4px; }
    window.freexp .freexp-menu-item { background: #f7fbff; color: #173f70; border: 1px solid #a9c4e6; border-radius: 5px; padding: 7px 12px; }
    window.freewin11 { background: #eef4fc; color: #172b45; }
    window.freewin11 headerbar { background: rgba(247,250,255,.94); color: #142b49; border-bottom: 1px solid #b8cbe2; }
    window.freewin11 .sidebar { background: linear-gradient(180deg,#f5f8ff,#dce9fa); }
    window.freewin11 .brand { color: #155dbb; }
    window.freewin11 .nav-button { background: #e8f1ff; color: #21466f; border: 1px solid #c5d8f0; border-radius: 10px; }
    window.freewin11 .nav-button:hover { background: #d6e8ff; }
    window.freewin11 .hero { color: #173e69; }
    window.freewin11 .muted { color: #506a89; }
    window.freewin11 .app-card { background: rgba(255,255,255,.88); border: 1px solid #c5d7ec; border-radius: 16px; }
    window.freewin11 .app-glyph { color: #176bd1; }
    window.freewin11 .app-name { color: #193c63; }
    window.freewin11 .app-detail { color: #526b88; }
    window.freewin11 button.accent { background: #176bd1; color: white; border-radius: 10px; }
    window.freewin11 .footer { background: #e2edf9; color: #24476c; }
    window.freewin11 .freewin11-taskbar { background: rgba(238,245,255,.92); border-top: 1px solid #bdcfe4; padding: 7px 12px; }
    window.freewin11 .freewin11-start { background: #176bd1; color: white; border: 0; border-radius: 10px; padding: 7px 18px; font-weight: 700; }
    window.freewin11 .freewin11-quick { background: #f7faff; color: #24476c; border: 1px solid #c5d7ec; border-radius: 8px; padding: 7px 12px; }
    window.freewin11 .freewin11-menu { background: #f7faff; border: 1px solid #c5d7ec; border-radius: 14px; padding: 12px; }
    window.freewin11 .freewin11-menu-item { background: #ffffff; color: #24476c; border: 1px solid #c5d7ec; border-radius: 9px; padding: 8px 12px; }
    window.freewin11 .freewin11-menu-item:hover { background: #e5f0ff; }
  )CSS";
  GdkDisplay* display = gdk_display_get_default();
  if (!display) return;
  GtkCssProvider* provider = gtk_css_provider_new();
#if GTK_CHECK_VERSION(4, 12, 0)
  gtk_css_provider_load_from_string(provider, css);
#else
  gtk_css_provider_load_from_data(provider, css, -1);
#endif
  gtk_style_context_add_provider_for_display(
      display, GTK_STYLE_PROVIDER(provider), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
  g_object_unref(provider);
}

void activate(GtkApplication* app, gpointer) {
  install_style();
  GtkWidget* window = gtk_application_window_new(app);
  gtk_window_set_title(GTK_WINDOW(window), desktop_name());
  gtk_window_set_default_size(GTK_WINDOW(window), 1280, 800);
  const bool marine = std::strcmp(desktop_id, "marine") == 0;
  const bool freexp = std::strcmp(desktop_id, "freexp") == 0;
  const bool freewin11 = std::strcmp(desktop_id, "freewin11") == 0;
  gtk_widget_add_css_class(window, marine ? "marine" : (freexp ? "freexp" : (freewin11 ? "freewin11" : "aurora")));

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
  GtkWidget* brand = gtk_label_new(marine ? "MARINE  •  WORKSPACE" :
      (freexp ? "FREEXP  •  CLASSIC WORKSPACE" : (freewin11 ? "FREEWIN11  •  MODERN WORKSPACE" : "AURORA  •  WORKSPACE")));
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
  GtkWidget* heading = gtk_label_new(marine ? "Your workspace, at a glance" :
      (freexp ? "Welcome back to your desktop" : (freewin11 ? "A familiar, focused workspace" : "A calmer place to work")));
  gtk_widget_set_halign(heading, GTK_ALIGN_START);
  gtk_widget_add_css_class(heading, "hero");
  gtk_box_append(GTK_BOX(content), heading);
  GtkWidget* subtitle = gtk_label_new(freexp
      ? "FreeXP classic shell • Start menu, taskbar and DOS application shortcut"
      : (freewin11
          ? "FreeWin11 desktop personality • Fluent-inspired launcher and host application shortcuts"
          : "Native GTK4 shell • launches delegate to installed host services"));
  gtk_widget_set_halign(subtitle, GTK_ALIGN_START);
  gtk_widget_add_css_class(subtitle, "muted");
  gtk_box_append(GTK_BOX(content), subtitle);

  GtkWidget* grid = gtk_grid_new();
  gtk_grid_set_row_spacing(GTK_GRID(grid), 16);
  gtk_grid_set_column_spacing(GTK_GRID(grid), 16);
  gtk_widget_set_vexpand(grid, TRUE);
  gtk_box_append(GTK_BOX(content), grid);
  gtk_grid_attach(GTK_GRID(grid), app_card("⌘", "Terminal",
      "Run commands using an installed terminal emulator.", "terminal", "terminal"), 0, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("▣", "Files",
      "Open your home folder with the host file handler.", "files", "aurora-files"), 1, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("◎", "Web",
      "Open a URL using the configured browser handler.", "browser", "chromium"), 2, 0, 1, 1);
  gtk_grid_attach(GTK_GRID(grid), app_card("⚙", "Settings",
      "Open host settings when the provider is installed.", "settings", "settings"), 0, 1, 1, 1);
  if (freexp) {
    gtk_grid_attach(GTK_GRID(grid), app_card("▣", "DOS Applications",
        "Launch DOSBox or DOSBox-X when an emulator provider is installed.",
        "dos", "terminal"), 1, 1, 1, 1);
  }

  if (freexp || freewin11) {
    GtkWidget* taskbar = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_widget_add_css_class(taskbar, freewin11 ? "freewin11-taskbar" : "freexp-taskbar");
    GtkWidget* start_button = gtk_menu_button_new();
    gtk_menu_button_set_label(GTK_MENU_BUTTON(start_button), "Start");
    gtk_widget_add_css_class(start_button, freewin11 ? "freewin11-start" : "freexp-start");
    GtkWidget* popover = gtk_popover_new();
    GtkWidget* start_menu = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    gtk_widget_add_css_class(start_menu, freewin11 ? "freewin11-menu" : "freexp-start-menu");
    GtkWidget* menu_title = gtk_label_new("All Programs");
    gtk_widget_add_css_class(menu_title, freewin11 ? "muted" : "freexp-menu-title");
    gtk_box_append(GTK_BOX(start_menu), menu_title);
    gtk_box_append(GTK_BOX(start_menu), action_button("Terminal", "terminal", freewin11 ? "freewin11-menu-item" : "freexp-menu-item"));
    gtk_box_append(GTK_BOX(start_menu), action_button("File Explorer", "files", freewin11 ? "freewin11-menu-item" : "freexp-menu-item"));
    gtk_box_append(GTK_BOX(start_menu), action_button("Internet", "browser", freewin11 ? "freewin11-menu-item" : "freexp-menu-item"));
    gtk_box_append(GTK_BOX(start_menu), action_button("Control Panel", "settings", freewin11 ? "freewin11-menu-item" : "freexp-menu-item"));
    if (freexp) gtk_box_append(GTK_BOX(start_menu), action_button("DOS Applications", "dos", "freexp-menu-item"));
    else gtk_box_append(GTK_BOX(start_menu), action_button("System Monitor", "settings", "freewin11-quick"));
    gtk_popover_set_child(GTK_POPOVER(popover), start_menu);
    gtk_menu_button_set_popover(GTK_MENU_BUTTON(start_button), popover);
    gtk_box_append(GTK_BOX(taskbar), start_button);
    gtk_box_append(GTK_BOX(taskbar), action_button("Files", "files", freewin11 ? "freewin11-quick" : "freexp-quick"));
    gtk_box_append(GTK_BOX(taskbar), action_button("Terminal", "terminal", freewin11 ? "freewin11-quick" : "freexp-quick"));
    gtk_box_append(GTK_BOX(taskbar), action_button("Web", "browser", freewin11 ? "freewin11-quick" : "freexp-quick"));
    GtkWidget* taskbar_spacer = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    gtk_widget_set_hexpand(taskbar_spacer, TRUE);
    gtk_box_append(GTK_BOX(taskbar), taskbar_spacer);
    GtkWidget* taskbar_status = gtk_label_new(freewin11 ? "Chimera II  •  FreeWin11" : "Chimera II  •  FreeXP");
    gtk_widget_add_css_class(taskbar_status, freewin11 ? "muted" : "freexp-menu-title");
    gtk_box_append(GTK_BOX(taskbar), taskbar_status);
    gtk_box_append(GTK_BOX(root), taskbar);
  }

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
      if (std::strcmp(value, "aurora") == 0 || std::strcmp(value, "marine") == 0 ||
          std::strcmp(value, "freexp") == 0 || std::strcmp(value, "freewin11") == 0)
        desktop_id = value;
      else {
        g_printerr("Unknown desktop '%s'; use aurora, marine, freexp or freewin11.\n", value);
        return 2;
      }
    } else if (std::strcmp(argv[i], "--self-test") == 0) {
      self_test = true;
    } else {
      g_printerr("Usage: %s [--desktop=aurora|marine|freexp|freewin11] [--self-test]\n", argv[0]);
      return 2;
    }
  }
  GtkApplication* app = gtk_application_new(
      "org.chimera.desktop.shell", G_APPLICATION_NON_UNIQUE);
  g_signal_connect(app, "activate", G_CALLBACK(activate), nullptr);
  char* app_argv[] = {argv[0], nullptr};
  const int result = g_application_run(G_APPLICATION(app), 1, app_argv);
  g_object_unref(app);
  if (self_test && semantic_icon_failures != 0) {
    g_printerr("Semantic SVG icon load failures: %d\\n", semantic_icon_failures);
    return 3;
  }
  return result;
}
