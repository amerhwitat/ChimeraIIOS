package chimera.services;
import java.util.*;
public final class ServiceRegistry {
  public static Optional<Service> resolve(List<Service> services,String id,String platform){ return services.stream().filter(s->s.id().equals(id)&&s.platform().equals(platform)).findFirst(); }
}
