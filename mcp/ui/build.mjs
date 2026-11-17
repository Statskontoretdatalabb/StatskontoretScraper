import {build} from 'esbuild';
import {readFileSync,writeFileSync} from 'node:fs';
const result = await build({entryPoints:[new URL('./app.js',import.meta.url).pathname],bundle:true,format:'iife',minify:true,write:false});
const template=readFileSync(new URL('./template.html',import.meta.url),'utf8');
writeFileSync(new URL('../comparison.html',import.meta.url),template.replace('/* APP_BUNDLE */',()=>result.outputFiles[0].text.replaceAll('</script','<\\/script')));
