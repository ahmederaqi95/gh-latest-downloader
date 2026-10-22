@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title GitHub Latest Downloader

rem ==================================================================
rem  SETTINGS - edit the values between the quotes
rem ==================================================================
rem  URL      GitHub user / organization / repo link
rem  OUT_DIR  folder where downloaded files are saved
rem  OPTIONS  extra options, for example:
rem             --dry-run             preview only, download nothing
rem             --no-forks            skip forked repositories
rem             --source-fallback     get the source zip when no release file fits
rem             --prefer zip,exe      preferred file types, best first
rem ==================================================================
set "URL=https://github.com/storytold"
set "OUT_DIR=downloads"
set "OPTIONS="
rem ==================================================================

rem GitHub allows only 60 API requests per hour without a token, which is not
rem enough for users with many repos. To use a token, remove "rem " below and
rem paste yours. Never commit or share a file that contains a real token.
rem set "GITHUB_TOKEN=ghp_xxxxxxxx"

rem A link given on the command line overrides the one above:
rem   run.bat https://github.com/some-user
if not "%~1"=="" set "URL=%~1"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto :nopython

echo.
echo  Link   : %URL%
echo  Output : %OUT_DIR%
echo.

%PY% "%~dp0get_latest.py" "%URL%" --dir "%OUT_DIR%" %OPTIONS%
set "RC=%ERRORLEVEL%"
goto :end

:nopython
echo Python 3.9 or newer was not found.
echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
set "RC=9009"

:end
echo.
echo Finished (exit code %RC%).
if not defined NO_PAUSE pause
exit /b %RC%
