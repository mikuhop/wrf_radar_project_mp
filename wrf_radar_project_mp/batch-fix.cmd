rem python isabel_main.py 0
rem python isabel_main.py 1
rem python isabel_main.py 2
rem python isabel_main.py 3
rem cd /d C:\Users\sugar\Desktop\wrf3.6.1\ARWH_KainFritschCu_Morrison\reflec_netcdf
rem postrun.cmd
rem cd /d C:\Users\sugar\Desktop\wrf3.6.1\ARWH_KainFritschCu_WSM6\reflec_netcdf
rem call postrun.cmd
cd /d C:\Users\sugar\Desktop\wrf3.6.1\ARWH_TiedtkeCu_Morrison\reflec_netcdf
call postrun.cmd
cd /d C:\Users\sugar\Desktop\wrf3.6.1\ARWH_TiedtkeCu_WSM6\reflec_netcdf
call postrun.cmd
cd /d C:\Users\sugar\Desktop\wrf3.6.1
"C:\Program Files\7-Zip\7z.exe" a wrf_bias.7z -ir!*.csv -xr!refl_3*
