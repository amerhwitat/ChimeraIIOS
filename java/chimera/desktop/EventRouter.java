package chimera.desktop;

import java.util.EnumMap;
import java.util.function.Consumer;

public final class EventRouter {
    private final EnumMap<DesktopEvent.Type, Consumer<DesktopEvent>> handlers = new EnumMap<>(DesktopEvent.Type.class);
    public void on(DesktopEvent.Type type, Consumer<DesktopEvent> handler) { handlers.put(type, handler); }
    public void dispatch(DesktopEvent event) { var handler = handlers.get(event.type()); if (handler != null) handler.accept(event); }
}
