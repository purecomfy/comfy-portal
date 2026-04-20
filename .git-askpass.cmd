@echo off
set prompt=%1
echo %prompt% | findstr /I "Username" >nul
if %errorlevel%==0 (
  echo x-access-token
) else (
  echo %GITHUB_TOKEN%
)
