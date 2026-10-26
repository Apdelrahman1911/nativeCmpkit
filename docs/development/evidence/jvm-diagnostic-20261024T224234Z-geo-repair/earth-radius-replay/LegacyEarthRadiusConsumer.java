import com.mohamedrejeb.calf.geo.LatLng;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

/** Separate source/JVM-field characterization, not a release or whole-ABI test. */
public final class LegacyEarthRadiusConsumer {
    public static void main(String[] args) throws Exception {
        // javac inlines the OLD public constant: this alone does not require a runtime field.
        double inlined = LatLng.EarthRadius;
        if (inlined != 6371.0d) throw new AssertionError("Unexpected baseline value");
        System.out.println("inlined_radius=" + inlined);
        Field field = LatLng.class.getField("EarthRadius");
        if (!Modifier.isStatic(field.getModifiers()) || !Modifier.isFinal(field.getModifiers())
                || field.getDouble(null) != inlined) throw new AssertionError("Public field contract");
        System.out.println("public_field_value_matches_baseline=true");
    }
}
