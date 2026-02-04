@echo off
echo --- GITHUB SENKRONIZASYON ARACI ---
git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Senkronizasyon sirasinda bir sorun oluştu. 
    echo Lutfen cakismalari kontrol edin veya destek alin.
) else (
    echo [BASARILI] Bilgisayarinizdaki dosyalar GitHub ile esitlendi.
)
pause
