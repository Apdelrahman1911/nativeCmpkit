// Focused tooling probe: actual Gradle9.7.1/AGP9.4.0 methods.
// Device connectors are synthetic serial-only discovery fixtures. No ADB/device tests run.
import java.io.File;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.gradle.api.internal.provider.DefaultListProperty;
import org.gradle.api.internal.provider.PropertyHost;
import com.android.builder.testing.api.DeviceProvider;
import com.android.build.gradle.internal.testing.ConnectedDevice;
import com.android.build.gradle.internal.testing.ConnectedDeviceProvider;
import com.android.build.gradle.internal.tasks.DeviceProviderInstrumentTestTask;
import com.android.ddmlib.IDevice;
public final class SerialContractProbe {
    private static ConnectedDevice device(String serial) {
        IDevice fixture=(IDevice)Proxy.newProxyInstance(IDevice.class.getClassLoader(),new Class[]{IDevice.class},(proxy,method,args)->{
            if(method.getName().equals("getSerialNumber")) return serial;
            throw new AssertionError("Unmodelled discovery-fixture operation: "+method.getName());
        });
        return new ConnectedDevice(fixture,null,1000,TimeUnit.MILLISECONDS);
    }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Exception {
        System.out.println("ACTUAL_PROPERTY_CLASS_SOURCE "+DefaultListProperty.class.getProtectionDomain().getCodeSource().getLocation());
        System.out.println("ACTUAL_AGP_CLASS_SOURCE "+DeviceProviderInstrumentTestTask.class.getProtectionDomain().getCodeSource().getLocation());
        ConnectedDeviceProvider provider=new ConnectedDeviceProvider(new File("no-adb-executed"),1000,null,null);
        Field field=ConnectedDeviceProvider.class.getDeclaredField("localDevices");field.setAccessible(true);
        List<ConnectedDevice> devices=(List<ConnectedDevice>)field.get(provider);
        devices.add(device("emulator-5588"));devices.add(device("emulator-5590"));
        Method filter=DeviceProviderInstrumentTestTask.class.getDeclaredMethod("getFilteredDevices",DeviceProvider.class,List.class);
        filter.setAccessible(true);
        for(boolean mutableInput:new boolean[]{false,true}) {
            DefaultListProperty<String> property=new DefaultListProperty<>(PropertyHost.NO_OP,String.class);
            property.addAll(mutableInput?new ArrayList<>(List.of("emulator-5588")):List.of("emulator-5588"));
            List<String> observed=property.get();
            try {filter.invoke(null,provider,observed);throw new AssertionError("Expected actual immutable-list mutation failure");}
            catch(InvocationTargetException error) {
                if(!(error.getCause() instanceof UnsupportedOperationException))throw error;
                System.out.println("ACTUAL_AGP_REPRO mutable_setter_input="+mutableInput+" property_result="+observed.getClass().getName()+" cause="+error.getCause().getClass().getName());
                error.getCause().printStackTrace(System.out);
            }
            if(!observed.equals(List.of("emulator-5588")))throw new AssertionError("Property result should stay unchanged");
        }
        DefaultListProperty<String> empty=new DefaultListProperty<>(PropertyHost.NO_OP,String.class);empty.empty();
        Object result=filter.invoke(null,provider,empty.get());
        if(result!=devices||((List<?>)result).size()!=2)throw new AssertionError("Empty target option must preserve already-selected connected provider");
        System.out.println("ACTUAL_AGP_EMPTY_OPTIONS_PRESERVE_PROVIDER passed; provider fixture is not real ADB selection");
        List<String> directMutable=new ArrayList<>(List.of("emulator-5588"));
        List<?> selected=(List<?>)filter.invoke(null,provider,directMutable);
        if(selected.size()!=1||!directMutable.isEmpty())throw new AssertionError("Actual method must consume matching mutable serial");
        System.out.println("ACTUAL_AGP_FILTER_CONSUMES_MATCHING_SERIAL passed");
    }
}
