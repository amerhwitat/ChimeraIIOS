#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

namespace aurora::context_menu {
enum class Surface { File, Folder, MultiSelection, EmptySpace, DesktopEmptySpace, WindowChrome };

struct Item { std::string label; std::string action; bool submenu{false}; bool destructive{false}; };

static Item item(const char* label,const char* action,bool submenu=false,bool destructive=false) {
    return {label,action,submenu,destructive};
}

std::vector<Item> build(Surface surface) {
    switch (surface) {
    case Surface::File:
        return {
            item("Open","open"), item("Open With","open-with",true),
            item("Open in New Window","open-new-window"), item("Cut","cut"),
            item("Copy","copy"), item("Paste","paste"), item("Rename","rename"),
            item("Move to","move-to",true), item("Copy to","copy-to",true),
            item("Create Shortcut","create-shortcut"), item("Send to","send-to",true),
            item("Add to Favorites","favorite"), item("Tags","tags",true),
            item("Calculate Size","size"), item("Hash","hash"),
            item("Permissions","permissions",true), item("Properties","properties"),
            item("Delete","delete",false,true)
        };
    case Surface::Folder:
        return {
            item("Open","open"), item("Open in New Window","open-new-window"),
            item("Open in Terminal","open-terminal"), item("Cut","cut"),
            item("Copy","copy"), item("Paste","paste"), item("Rename","rename"),
            item("Move to","move-to",true), item("Copy to","copy-to",true),
            item("Create Shortcut","create-shortcut"), item("Send to","send-to",true),
            item("Add to Favorites","favorite"), item("Tags","tags",true),
            item("Calculate Recursive Size","recursive-size"),
            item("Count Files","count-files"), item("Count Directories","count-directories"),
            item("Permissions","permissions",true), item("Properties","properties"),
            item("Delete","delete",false,true)
        };
    case Surface::MultiSelection:
        return {
            item("Open","open"), item("Open With","open-with",true),
            item("Cut","cut"), item("Copy","copy"), item("Paste","paste"),
            item("Move to","move-to",true), item("Copy to","copy-to",true),
            item("Send to","send-to",true), item("Add to Favorites","favorite"),
            item("Compress","compress",true), item("Create Archive","archive"),
            item("Share","share",true), item("Compare","compare"),
            item("Hash","hash"), item("Properties","properties"),
            item("Delete","delete",false,true)
        };
    case Surface::EmptySpace:
    case Surface::DesktopEmptySpace:
        return {
            item("New Folder","new-folder",true), item("New Document","new-document",true),
            item("Paste","paste"), item("Paste Shortcut","paste-shortcut"),
            item("Undo","undo"), item("Redo","redo"), item("Select All","select-all"),
            item("Refresh","refresh"), item("Open in Terminal","open-terminal"),
            item("View","view",true), item("Sort By","sort-by",true),
            item("Group By","group-by",true), item("Show Hidden Files","toggle-hidden"),
            item("Show File Extensions","toggle-extensions"),
            item("Show Thumbnails","toggle-thumbnails"), item("Arrange Icons","arrange",true),
            item("Icon Size","icon-size",true), item("Auto Arrange","auto-arrange"),
            item("Snap to Grid","snap-grid"), item("New Window","new-window"),
            item("Display / الشاشة","display",true),
            item("Display Settings / إعدادات الشاشة","display-settings"),
            item("Resolution / الدقة","display-resolution"),
            item("Graphics Drivers / تعريفات الرسومات","gpu-drivers"),
            item("Personalization","personalization"),
            item("Folder Options","folder-options"), item("Properties","properties")
        };
    case Surface::WindowChrome:
        return {
            item("Restore","restore"), item("Move","move"), item("Size","size"),
            item("Minimize","minimize"), item("Maximize","maximize"), item("Always on Top","always-on-top"),
            item("Center Window","center"), item("Move to Workspace","workspace",true),
            item("Snap Left","snap-left"), item("Snap Right","snap-right"),
            item("Snap Top","snap-top"), item("Snap Bottom","snap-bottom"),
            item("Fullscreen","fullscreen"), item("Close","close",false,true)
        };
    }
    return {};
}

const char* surface_name(Surface surface) {
    switch (surface) {
    case Surface::File: return "file";
    case Surface::Folder: return "folder";
    case Surface::MultiSelection: return "multi-selection";
    case Surface::EmptySpace: return "empty-space";
    case Surface::DesktopEmptySpace: return "desktop-empty-space";
    case Surface::WindowChrome: return "window-chrome";
    }
    return "unknown";
}

void print(Surface surface) {
    std::printf("Aurora context menu: %s\n", surface_name(surface));
    for (const auto& entry : build(surface))
        std::printf("  %s [%s]%s\n", entry.label.c_str(), entry.action.c_str(),
                    entry.submenu ? " >" : "");
}
}

int main(int argc,char** argv) {
    using namespace aurora::context_menu;
    Surface surface=Surface::EmptySpace;
    if (argc>1) {
        const std::string arg=argv[1];
        if(arg=="file") surface=Surface::File;
        else if(arg=="folder") surface=Surface::Folder;
        else if(arg=="multi") surface=Surface::MultiSelection;
        else if(arg=="desktop") surface=Surface::DesktopEmptySpace;
        else if(arg=="window") surface=Surface::WindowChrome;
    }
    print(surface);
    return 0;
}
