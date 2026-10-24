#!/usr/bin/env python3
"""Compile a baseline pure-Kotlin subset using already cached compiler jars.
No Gradle invocation, downloads, publication, or repository source edits.
Arguments: --cache PATH optionally points to a Gradle modules-2/files-2.1 cache.
"""
from pathlib import Path
import argparse, subprocess, tempfile, os
parser=argparse.ArgumentParser()
parser.add_argument('--cache',type=Path,default=Path(os.environ.get('GRADLE_USER_HOME',Path.home()/'.gradle'))/'caches/modules-2/files-2.1')
args=parser.parse_args()
coords=[('org.jetbrains.kotlin','kotlin-compiler-embeddable','2.4.20'),('org.jetbrains.kotlin','kotlin-build-tools-api','2.4.20'),('org.jetbrains.kotlin','kotlin-stdlib','2.4.20'),('org.jetbrains.kotlin','kotlin-script-runtime','2.4.20'),('org.jetbrains.kotlin','kotlin-reflect','1.6.10'),('org.jetbrains.kotlin','kotlin-daemon-embeddable','2.4.20'),('org.jetbrains.kotlinx','kotlinx-coroutines-core-jvm','1.8.0'),('org.jetbrains','annotations','13.0')]
jars=[]
for g,a,v in coords:
 matches=sorted((args.cache/g/a/v).glob(f'*/{a}-{v}.jar'))
 if not matches: raise SystemExit(f'Missing cached dependency {g}:{a}:{v}; no download attempted')
 jars.append(str(matches[0]))
cp=':'.join(jars)
stdlib=jars[2]
base='af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6'
with tempfile.TemporaryDirectory(prefix='nativecmpkit-nav-audit-') as temp:
 work=Path(temp); sources=[]
 for f in ['AdaptiveBaseBundle.kt','AdaptiveBundle.kt','AdaptiveNavType.kt','NavArgument.kt']:
  p=work/f
  p.write_bytes(subprocess.check_output(['git','show',f'{base}:calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/{f}']))
  sources.append(str(p))
 cmd=['java','-Xmx512m','-cp',cp,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-classpath',stdlib,'-d',str(work/'repro.jar'),*sources,str(Path(__file__).with_name('Repro.kt'))]
 subprocess.run(cmd,check=True)
 subprocess.run(['java','-cp',str(work/'repro.jar')+':'+stdlib,'com.mohamedrejeb.calf.navigation.ReproKt'],check=True)
