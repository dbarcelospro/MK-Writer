@echo off
chcp 65001 >nul
echo Instalando atalho do MK Writer na Area de Trabalho...

set SCRIPT="%TEMP%\mk_writer_shortcut_%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\MK Writer.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0MK-Writer.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.Description = "MK Writer - Editor e Compilador Academico ABNT" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ========================================================
echo   Atalho do MK Writer criado na Area de Trabalho!
echo ========================================================
echo.
pause
