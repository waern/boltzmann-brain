{ mkDerivation, aeson, base, bytestring, containers, directory
, edit-distance, filepath, haskell-src-exts, hmatrix, megaparsec
, MonadRandom, mtl, multiset, paganini-hs, pretty-terminal, process
, random, stdenv, template-haskell, text, time, transformers
}:
mkDerivation {
  pname = "boltzmann-brain";
  version = "2.0";
  src = ./.;
  isLibrary = true;
  isExecutable = true;
  libraryHaskellDepends = [
    aeson base bytestring containers edit-distance haskell-src-exts
    hmatrix megaparsec MonadRandom mtl multiset paganini-hs
    pretty-terminal process random template-haskell text time
    transformers
  ];
  executableHaskellDepends = [
    aeson base bytestring containers directory filepath megaparsec text
  ];
  homepage = "https://github.com/maciej-bendkowski/boltzmann-brain";
  description = "Analytic sampler compiler for combinatorial systems";
  license = stdenv.lib.licenses.bsd3;
}
