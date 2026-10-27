from pathlib import Path
import sys,json,hashlib,subprocess,datetime as dt
ROOT=Path('/root/projects/nativeCmpKit');OUT=ROOT/'build/android-serial-contract-20261027-003'
sys.path.insert(0,str(ROOT/'scripts/ci'));import library_tests as lt
assert not OUT.exists();OUT.mkdir();before=lt.snapshot_inputs(ROOT)
(OUT/'inputs-before.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
base=next(Path('/root/.gradle/wrapper/dists/gradle-9.7.1-bin').glob('*/gradle-9.7.1/lib'))
# Gradle's lib/api contains compile-only stubs; never put it on the executable classpath.
cp=list(sorted(p for p in base.rglob('*.jar') if 'api' not in p.relative_to(base).parts))
modules=Path('/root/.gradle/caches/modules-2/files-2.1')
for group in ['com.android.tools.build','com.android.tools','com.android.tools.ddms','com.android.tools.utp','com.android.tools.analytics-library']:
 for p in (modules/group).rglob('*.jar'):
  if p.parts[-3] in {'9.4.0','32.4.0'}:cp.append(p)
for group,name,version in [('org.jetbrains.kotlin','kotlin-stdlib','2.4.20'),('com.google.protobuf','protobuf-java','')]:
 ps=[p for p in (modules/group/name).rglob('*.jar') if not version or version in p.parts]
 if ps:cp.append(sorted(ps)[-1])
classpath=':'.join(str(p) for p in cp)
source='''// Focused tooling probe: actual Gradle9.7.1/AGP9.4.0 methods.
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
'''
(OUT/'SerialContractProbe.java').write_text(source)
results=[]
for label,cmd in [('compile',['/usr/lib/jvm/java-17-openjdk-amd64/bin/javac','-classpath',classpath,'-d',str(OUT),str(OUT/'SerialContractProbe.java')]),('actual-probe',['/usr/lib/jvm/java-17-openjdk-amd64/bin/java','-classpath',str(OUT)+':'+classpath,'SerialContractProbe'])]:
 log=OUT/(label+'.log');result=lt.execute(ROOT,cmd,log,90,8192);results.append({'name':label,'execution':result,'log_sha256':lt.sha256(log) if log.exists() else None})
 print(label,result)
 if result['exit_code']!=0:print(log.read_text(errors='replace')[-5000:] if log.exists() else 'No log');break
if len(results)==2 and all(r['execution']['exit_code']==0 for r in results):print((OUT/'actual-probe.log').read_text())
after=lt.snapshot_inputs(ROOT);(OUT/'inputs-after.json').write_text(json.dumps(after,indent=2,sort_keys=True)+'\n')
java_version=subprocess.check_output(['/usr/lib/jvm/java-17-openjdk-amd64/bin/java','-version'],stderr=subprocess.STDOUT,text=True)
receipt={'java_version':java_version,'java_executable':'/usr/lib/jvm/java-17-openjdk-amd64/bin/java','javac_executable':'/usr/lib/jvm/java-17-openjdk-amd64/bin/javac','observed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_revision':lt.git_revision(ROOT),'source_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)), 'source_input_count':len(before),'changed_inputs':[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)],'results':results,'production_device_tests_executed':0,'synthetic_tooling_probe_cases':4 if len(results)==2 and results[-1]['execution']['exit_code']==0 else 0,'dependencies':[{'path':str(p),'sha256':lt.sha256(p)} for p in cp],'driver_sha256':lt.sha256(Path(__file__)),'probe_source_sha256':lt.sha256(OUT/'SerialContractProbe.java'),'scope':'Actual cached AGP/Gradle Java method invocations; synthetic serial-only connected-device entries. No ADB discovery, emulator, instrumentation, library functionality or dependency provenance certification. Mutable setter input still returns immutable Gradle property results.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
