-- | Author: Maciej Bendkowski <maciej.bendkowski@tcs.uj.edu.pl>
module Main (main) where

import System.IO
import System.Exit
import System.Console.GetOpt
import System.Environment
    
import Data.List (nub)

import System
import Parser
import Oracle
import Compiler

data Flag = Epsilon String
          | ModuleName String
          | Version
          | Help
            deriving (Eq)

options :: [OptDescr Flag]
options = [Option "e" ["eps"] (ReqArg Epsilon "e")
            "Approximation error bound. Defaults to 1.0e-6.",
           
           Option "m" ["module"] (ReqArg ModuleName "m")
            "The resulting Haskell module name. Defaults to Main.",

           Option "v" ["version"] (NoArg Version)
            "Prints the program version number.",

           Option "h?" ["help"] (NoArg Help)
            "Prints this help message."]

usageHeader :: String
usageHeader = "Usage: bb [OPTIONS...]"

versionHeader :: String
versionHeader = "boltzmann-brain ALPHA version (c) Maciej Bendkowski 2016"

getEpsilon :: [Flag] -> Double
getEpsilon (Epsilon eps : _) = read eps
getEpsilon (_:fs) = getEpsilon fs
getEpsilon [] = 1.0e-6

getModuleName :: [Flag] -> String
getModuleName (ModuleName name : _) = name
getModuleName (_:fs) = getModuleName fs
getModuleName [] = "Main"

parse :: [String] -> IO ([Flag], [String])
parse argv = case getOpt Permute options argv of 
               (ops, nonops, [])
                    | Help `elem` ops -> do
                        putStr $ usageInfo usageHeader options
                        exitSuccess
                    | Version `elem` ops -> do
                        putStrLn versionHeader
                        exitSuccess
                    | otherwise -> return (nub (concatMap mkset ops), fs)
                        where
                            fs = if null nonops then [] else nonops
                            mkset x = [x]
               (_, _, errs) -> do
                    hPutStr stderr (concat errs ++ usageInfo usageHeader options)
                    exitWith (ExitFailure 1)

run :: [Flag] 
    -> String 
    -> IO ()

run flags f = do
    sys <- parseSystem f
    case sys of
      Left err -> printError err
      Right sys -> runCompiler eps module' sys
    where
        module' = getModuleName flags
        eps = getEpsilon flags

runCompiler eps module' sys = case consistent sys of
    Left err -> reportSystemError err
    Right _ -> do
        let sys' = toBoltzmann sys eps
        compile sys' module'

main :: IO ()
main = do
    (ops, fs) <- getArgs >>= parse
    mapM_ (run ops) fs
    exitSuccess