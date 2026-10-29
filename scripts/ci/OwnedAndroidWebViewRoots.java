// Test-only profiler output: class/field/root kinds, NEVER strings, IDs or raw heap values.
import java.io.File;
import java.util.*;
import org.graalvm.visualvm.lib.jfluid.heap.*;

public final class OwnedAndroidWebViewRoots {
    private static String quote(String value) {
        StringBuilder out = new StringBuilder("\"");
        for (char c : value.toCharArray()) {
            if (c == '\\' || c == '"') out.append('\\').append(c);
            else if (c < 32) out.append(String.format("\\u%04x", (int)c));
            else out.append(c);
        }
        return out.append('"').toString();
    }
    private static String type(Instance value) {
        return value == null ? "STATIC/NULL" : value.getJavaClass().getName();
    }
    private static String edge(Value value) {
        if (value instanceof FieldValue field)
            return field.getField().getDeclaringClass().getName() + "." + field.getField().getName();
        if (value instanceof ArrayItemValue) return "array-element";
        return value.getClass().getSimpleName();
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("One owned converted heap is required");
        Heap heap = HeapFactory.createHeap(new File(args[0]));
        List<String> targets = new ArrayList<>();
        for (String name : List.of("android.webkit.WebView",
                "com.mohamedrejeb.calf.ui.web.WebViewLifetimeActivity")) {
            JavaClass cls = heap.getJavaClassByName(name);
            if (cls == null) continue;
            if (cls.getInstancesCount() > 16) throw new IllegalStateException("Unexpected unbounded native target population");
            for (Instance target : cls.getInstances()) {
                List<String> path = new ArrayList<>();
                Set<Long> seen = new HashSet<>();
                Instance cursor = target;
                boolean rootReached = false, weakEdge = false;
                List<String> roots = new ArrayList<>();
                for (int depth = 0; depth < 64 && cursor != null && seen.add(cursor.getInstanceId()); depth++) {
                    if (cursor.isGCRoot()) {
                        rootReached = true;
                        for (GCRoot root : heap.getGCRoots(cursor)) roots.add(quote(root.getKind()));
                        break;
                    }
                    Instance parent = cursor.getNearestGCRootPointer();
                    List<String> fields = new ArrayList<>();
                    for (Value reference : cursor.getReferences()) {
                        Instance defining = reference.getDefiningInstance();
                        if (defining != null && parent != null && defining.getInstanceId() == parent.getInstanceId()) {
                            String field = edge(reference);
                            fields.add(quote(field));
                            if (field.equals("java.lang.ref.Reference.referent")) weakEdge = true;
                        }
                    }
                    path.add("{\"child_class\":" + quote(type(cursor)) + ",\"parent_class\":" + quote(type(parent)) +
                        ",\"fields\":[" + String.join(",", fields) + "]}");
                    cursor = parent;
                }
                targets.add("{\"target_class\":" + quote(name) + ",\"nearest_path\":[" + String.join(",", path) +
                    "],\"root_reached\":" + rootReached + ",\"weak_reference_edge\":" + weakEdge +
                    ",\"root_kinds\":[" + String.join(",", roots) + "]}");
            }
        }
        System.out.println("{\"schema_version\":1,\"scope\":\"Nearest heap root paths only; not all paths or native allocations\"," +
            "\"raw_ids_or_values_exported\":false,\"targets\":[" + String.join(",", targets) + "]}");
    }
}
