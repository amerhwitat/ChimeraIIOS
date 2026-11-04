// Native GTK4 shell for Aurora and Marine desktop personalities.
// This is a Linux/GTK user-space shell client, not a compositor or a Koronos
// syscall port. Koronos GUI readiness remains gated on real process execution,
// graphics/input services, and an OS-native compositor/session implementation.
#include <gtk/gtk.h>
#include <cstring>
#include <string>
#include <utility>

namespace {
const char* desktop_id = "aurora";
bool self_test = false;
GtkLabel* status_label = nullptr;
GtkWindow* main_window = nullptr;
GtkWidget* selected_card = nullptr;
guint pending_open_source = 0;

void card_pressed(GtkGestureClick*, int, double, double, gpointer);

struct RenameData { GtkWidget* label; GtkWidget* entry; };

void rename_response(GtkDialog* dialog, int response, gpointer user_data) {
  auto* data = static_cast<RenameData*>(user_data);
  if (response == GTK_RESPONSE_ACCEPT && data) {
    const char* value = gtk_editable_get_text(GTK_EDITABLE(data->entry));
    if (value && *value) gtk_label_set_text(GTK_LABEL(data->label), value);
    set_status("Desktop label updated for this session only; host files were not renamed.");
  }
  delete data;
  gtk_window_destroy(GTK_WINDOW(dialog));
}

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
  g_object_set_data(G_OBJECT(card),"name-label",name);
  g_object_set_data(G_OBJECT(card),"launch-action",const_cast<char*>(action));
  GtkWidget* description = gtk_label_new(detail);
  gtk_label_set_wrap(GTK_LABEL(description), TRUE);
  gtk_widget_add_css_class(description, "app-detail");
  gtk_box_append(GTK_BOX(card), icon);
  gtk_box_append(GTK_BOX(card), name);
  gtk_box_append(GTK_BOX(card), description);
  GtkWidget* open=action_button("Open", action, "accent");
  g_object_set_data(G_OBJECT(card),"open-button",open);
  gtk_box_append(GTK_BOX(card),open);
  GtkGesture* click=gtk_gesture_click_new();
  gtk_gesture_single_set_button(GTK_GESTURE_SINGLE(click),0);
  g_signal_connect(click,"pressed",G_CALLBACK(card_pressed),card);
  gtk_widget_add_controller(card,GTK_EVENT_CONTROLLER(click));
  return card;
}


void play_sound(const char* event){
  gchar* executable=g_find_program_in_path("canberra-gtk-play");
  if(!executable)return;
  gchar* argv[]={executable,const_cast<gchar*>("-i"),const_cast<gchar*>(event),nullptr};
  GError* error=nullptr;
  g_spawn_async(nullptr,argv,nullptr,G_SPAWN_SEARCH_PATH,nullptr,nullptr,nullptr,&error);
  if(error)g_error_free(error);
  g_free(executable);
}
void show_properties(GtkWidget* parent, const char* title) {
  GtkWidget* dialog=gtk_dialog_new();
  gtk_window_set_title(GTK_WINDOW(dialog),"Item Properties");
  gtk_window_set_transient_for(GTK_WINDOW(dialog),main_window);
  gtk_window_set_modal(GTK_WINDOW(dialog),TRUE);
  gtk_window_set_default_size(GTK_WINDOW(dialog),380,180);
  GtkWidget* content=gtk_dialog_get_content_area(GTK_DIALOG(dialog));
  GtkWidget* label=gtk_label_new((std::string("Application: ")+title+
      "\\nLaunch target is delegated to the host session. File operations are not implied.").c_str());
  gtk_label_set_wrap(GTK_LABEL(label),TRUE);
  gtk_widget_set_margin_top(label,20);gtk_widget_set_margin_bottom(label,20);
  gtk_widget_set_margin_start(label,20);gtk_widget_set_margin_end(label,20);
  gtk_box_append(GTK_BOX(content),label);
  gtk_dialog_add_button(GTK_DIALOG(dialog),"Close",GTK_RESPONSE_CLOSE);
  g_signal_connect(dialog,"response",G_CALLBACK(+[](GtkDialog* d,int,GtkWidget*){gtk_window_destroy(GTK_WINDOW(d));}),nullptr);
  gtk_window_present(GTK_WINDOW(dialog));
}

void rename_card(GtkWidget* card){
  if(!card){set_status("Select an application card first.");return;}
  GtkWidget* label=GTK_WIDGET(g_object_get_data(G_OBJECT(card),"name-label"));
  if(!label)return;
  GtkWidget* dialog=gtk_dialog_new();
  gtk_window_set_title(GTK_WINDOW(dialog),"Rename desktop item");
  gtk_window_set_transient_for(GTK_WINDOW(dialog),main_window);
  gtk_window_set_modal(GTK_WINDOW(dialog),TRUE);
  GtkWidget* area=gtk_dialog_get_content_area(GTK_DIALOG(dialog));
  GtkWidget* entry=gtk_entry_new();
  gtk_editable_set_text(GTK_EDITABLE(entry),gtk_label_get_text(GTK_LABEL(label)));
  gtk_widget_set_margin_top(entry,18);gtk_widget_set_margin_bottom(entry,18);
  gtk_widget_set_margin_start(entry,18);gtk_widget_set_margin_end(entry,18);
  gtk_box_append(GTK_BOX(area),entry);
  gtk_dialog_add_button(GTK_DIALOG(dialog),"Cancel",GTK_RESPONSE_CANCEL);
  gtk_dialog_add_button(GTK_DIALOG(dialog),"Rename",GTK_RESPONSE_ACCEPT);
  auto* rename_data = new RenameData{label, entry};
  g_signal_connect(dialog, "response", G_CALLBACK(rename_response), rename_data);
  gtk_window_present(GTK_WINDOW(dialog));
}
void context_action(GtkButton*,gpointer data){
  const char* action=static_cast<const char*>(data);
  if(std::strcmp(action,"properties")==0){
    GtkWidget* label=selected_card?GTK_WIDGET(g_object_get_data(G_OBJECT(selected_card),"name-label")):nullptr;
    show_properties(selected_card,label?gtk_label_get_text(GTK_LABEL(label)):"Selected application");
  }else if(std::strcmp(action,"rename")==0)rename_card(selected_card);
  else if(std::strcmp(action,"open")==0){
    const char* target=selected_card?static_cast<const char*>(g_object_get_data(G_OBJECT(selected_card),"launch-action")):nullptr;
    if(target)launch_clicked(nullptr,const_cast<char*>(target));
    else set_status("No application is selected.");
  }
}
void card_pressed(GtkGestureClick* gesture,int presses,double,double,gpointer data){
  GtkWidget* card=GTK_WIDGET(data);
  const guint button=gtk_gesture_single_get_current_button(GTK_GESTURE_SINGLE(gesture));
  if(button==3){
    selected_card=card;play_sound("menu-popup");
    GtkWidget* pop=gtk_popover_new();
    GtkWidget* list=gtk_box_new(GTK_ORIENTATION_VERTICAL,4);
    for(const auto& item : {std::pair<const char*,const char*>{"Open","open"},{"Rename","rename"},{"Properties","properties"}}){
      GtkWidget* b=gtk_button_new_with_label(item.first);
      g_signal_connect(b,"clicked",G_CALLBACK(context_action),const_cast<char*>(item.second));
      gtk_box_append(GTK_BOX(list),b);
    }
    gtk_popover_set_child(GTK_POPOVER(pop),list);
    gtk_widget_set_parent(pop,card);gtk_popover_popup(GTK_POPOVER(pop));
    return;
  }
  if(button!=1)return;
  selected_card=card;play_sound("click");
  GtkWidget* sibling=gtk_widget_get_first_child(gtk_widget_get_parent(card));
  while(sibling){gtk_widget_remove_css_class(sibling,"selected");sibling=gtk_widget_get_next_sibling(sibling);}
  gtk_widget_add_css_class(card,"selected");
  if(presses==2){
    if(pending_open_source)g_source_remove(pending_open_source);
    pending_open_source=g_timeout_add(280,[](gpointer data)->gboolean{
      GtkWidget* target=GTK_WIDGET(data);
      pending_open_source=0;
      GtkWidget* open=static_cast<GtkWidget*>(g_object_get_data(G_OBJECT(target),"open-button"));
      if(open){play_sound("complete");g_signal_emit_by_name(open,"clicked");}
      return G_SOURCE_REMOVE;
    },card);
  }else if(presses>=3){
    if(pending_open_source){g_source_remove(pending_open_source);pending_open_source=0;}
    play_sound("dialog-information");
    GtkWidget* label=GTK_WIDGET(g_object_get_data(G_OBJECT(card),"name-label"));
    show_properties(card,label?gtk_label_get_text(GTK_LABEL(label)):"Selected application");
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
    .app-card.selected { border: 2px solid #8fe5ee; box-shadow: 0 8px 24px #0008; }
    .app-card button { transition: background 120ms ease, box-shadow 120ms ease; }
    .app-card button:active { box-shadow: inset 0 2px 6px #0008; }
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


void desktop_menu_action(GSimpleAction* action,GVariant*,gpointer data){
  GtkApplication* app=GTK_APPLICATION(data);
  const char* name=g_action_get_name(G_ACTION(action));
  if(std::strcmp(name,"files")==0){launch_clicked(nullptr,const_cast<char*>("files"));return;}
  if(std::strcmp(name,"terminal")==0){launch_clicked(nullptr,const_cast<char*>("terminal"));return;}
  if(std::strcmp(name,"browser")==0){launch_clicked(nullptr,const_cast<char*>("browser"));return;}
  if(std::strcmp(name,"settings")==0){launch_clicked(nullptr,const_cast<char*>("settings"));return;}
  if(std::strcmp(name,"minimize")==0){if(main_window)gtk_window_minimize(main_window);return;}
  if(std::strcmp(name,"maximize")==0){if(main_window){if(gtk_window_is_maximized(main_window))gtk_window_unmaximize(main_window);else gtk_window_maximize(main_window);}return;}
  if(std::strcmp(name,"close")==0){if(main_window)gtk_window_close(main_window);return;}
  if(std::strcmp(name,"tile")==0||std::strcmp(name,"cascade")==0){set_status("Window tiling/cascading across applications is provided by the active Wayland compositor. Use its window overview or keyboard shortcuts.");return;}
  if(std::strcmp(name,"rename")==0){rename_card(selected_card);return;}
  if(std::strcmp(name,"properties")==0){show_properties(GTK_WIDGET(main_window),"Desktop workspace");return;}
  if(std::strcmp(name,"about")==0){show_properties(GTK_WIDGET(main_window),desktop_name());return;}
  if(std::strcmp(name,"refresh")==0){set_status("Desktop shell refreshed.");return;}
  (void)app;
}
void add_menu_action(GtkApplication* app,const char* name){
  GSimpleAction* action=g_simple_action_new(name,nullptr);
  g_signal_connect(action,"activate",G_CALLBACK(desktop_menu_action),app);
  g_action_map_add_action(G_ACTION_MAP(app),G_ACTION(action));
  g_object_unref(action);
}
GtkWidget* build_menu_bar(GtkApplication* app){
  const char* names[]={"files","terminal","browser","settings","rename","properties","refresh","tile","cascade","minimize","maximize","close","about"};
  for(const char* name:names)add_menu_action(app,name);
  GMenu* root=g_menu_new();
  const struct MenuDef{const char* title;const char* label;const char* action;} entries[]={
    {"File","Open Files","app.files"},{"File","Open Terminal","app.terminal"},
    {"Edit","Rename Selected","app.rename"},{"Edit","Properties","app.properties"},
    {"View","Refresh Desktop","app.refresh"},{"Window","Tile Windows","app.tile"},
    {"Window","Cascade Windows","app.cascade"},{"Window","Minimize","app.minimize"},
    {"Window","Maximize / Restore","app.maximize"},{"Window","Close","app.close"},
    {"Help","About","app.about"}};
  for(const char* menuName:{"File","Edit","View","Window","Help"}){
    GMenu* submenu=g_menu_new();
    for(const auto& entry:entries)if(std::strcmp(entry.title,menuName)==0)
      g_menu_append(submenu,entry.label,entry.action);
    if(std::strcmp(menuName,"File")==0){g_menu_append(submenu,"Open Browser","app.browser");g_menu_append(submenu,"Open Settings","app.settings");}
    g_menu_append_submenu(root,menuName,G_MENU_MODEL(submenu));
    g_object_unref(submenu);
  }
  GtkWidget* bar=gtk_popover_menu_bar_new_from_model(G_MENU_MODEL(root));
  g_object_unref(root);
  return bar;
}

void activate(GtkApplication* app, gpointer) {
  install_style();
  GtkWidget* window = gtk_application_window_new(app);
  gtk_window_set_title(GTK_WINDOW(window), desktop_name());
  gtk_window_set_default_size(GTK_WINDOW(window), 1280, 800);
  main_window=GTK_WINDOW(window);
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
  gtk_box_append(GTK_BOX(root),build_menu_bar(app));

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

  GtkWidget* scroller=gtk_scrolled_window_new();
  gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroller),GTK_POLICY_AUTOMATIC,GTK_POLICY_AUTOMATIC);
  gtk_widget_set_hexpand(scroller,TRUE);gtk_widget_set_vexpand(scroller,TRUE);
  gtk_box_append(GTK_BOX(body),scroller);
  GtkWidget* content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 18);
  gtk_widget_set_hexpand(content, TRUE);
  gtk_widget_set_margin_top(content, 28);
  gtk_widget_set_margin_bottom(content, 24);
  gtk_widget_set_margin_start(content, 30);
  gtk_widget_set_margin_end(content, 30);
  gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(scroller),content);
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
