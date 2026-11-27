#!/bin/bash -eu
# Builds each fuzz/*_fuzzer.py into $OUT for ClusterFuzzLite (workflow Fuzzing), as its documentation for Python says
# (https://google.github.io/clusterfuzzlite/build-integration/python-lang/): one PyInstaller package per target and a
# wrapper that runs it. Pure Python: no `pip install .` and no LD_PRELOAD of the sanitizer, which the documentation
# advises against for code without C extensions. Beside each target: its seed corpus and its dictionary, if any.
cd "$SRC/awesome-lego"
for fuzzer in fuzz/*_fuzzer.py; do
  name=$(basename -s .py "$fuzzer")
  base=${name%_fuzzer}
  pyinstaller --distpath "$OUT" --workpath "$WORK/$name" --specpath "$WORK/$name" --onefile --name "$name.pkg" \
    --paths "$PWD/scripts" --add-data "$PWD/data/brands.toml:data" "$fuzzer"
  chmod -x "$OUT/$name.pkg"   # only the wrapper is an executable, so that only it is taken for a fuzz target
  cat > "$OUT/$name" <<WRAPPER
#!/bin/sh
# LLVMFuzzerTestOneInput for fuzzer detection.
this_dir=\$(dirname "\$0")
chmod +x "\$this_dir/$name.pkg"
ASAN_OPTIONS=\$ASAN_OPTIONS:symbolize=1:external_symbolizer_path=\$this_dir/llvm-symbolizer:detect_leaks=0 "\$this_dir/$name.pkg" "\$@"
WRAPPER
  chmod +x "$OUT/$name"
  if [ -f "fuzz/$base.dict" ]; then cp "fuzz/$base.dict" "$OUT/$name.dict"; fi
  if [ -d "fuzz/seeds/$base" ]; then python3 -m zipfile -c "$OUT/${name}_seed_corpus.zip" fuzz/seeds/"$base"/*; fi
done
