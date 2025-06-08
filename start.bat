@echo off
REM ### Encoding and Unicode settings ###
REM �d�v: ���̃o�b�`�t�@�C�����̂��uShift_JIS (SJIS)�v�G���R�[�f�B���O�ŕۑ����Ă��������B
REM SJIS���Ŏ��s����ꍇ�A�R���\�[���̃R�[�h�y�[�W�̓f�t�H���g (932) �̂܂܂Ƃ��܂��B

setlocal EnableDelayedExpansion
REM �X�N���v�g�̂���f�B���N�g�����J�����g�f�B���N�g���ɂ���
pushd "%~dp0"
REM --- Configuration ---
REM PROJECT_DIR �� pushd �ɂ��J�����g�f�B���N�g�����v���W�F�N�g���[�g�ɂȂ邽�߁A�����ł̃p�X��`�ɂ͕s�v
set "VENV_DIR=venv"
set "SCR_DIR=open_mes\scr"
set "IMAGE_DIR=open_mes\image"
set "REQUIREMENTS_FILE=requirements.txt"
set "MANAGE_PY=%SCR_DIR%\manage.py"
set "ENV_FILE=%SCR_DIR%\.env"
set "ENV_EXAMPLE_FILE=%SCR_DIR%\.env.example"
set "SETUP_COMPLETE_FLAG_FILE=%VENV_DIR%\.setup_complete"

REM --- Title ---
title Open MES Project Windows �Z�b�g�A�b�v

echo =======================================================
echo  Open MES Project Windows �J�����Z�b�g�A�b�v
echo =======================================================
echo(

REM --- Check if setup has been completed ---
if exist "%SETUP_COMPLETE_FLAG_FILE%" (
    echo [+] �Z�b�g�A�b�v�͈ȑO�Ɋ������Ă��܂��B
    echo [+] �A�v���P�[�V�����̋N���ɐi�݂܂�...
    echo.
    goto :run_application
)

REM --- Initial Setup Process ---
echo ���̃X�N���v�g�́AWindows �Ńv���W�F�N�g�����s���邽�߂̃Z�b�g�A�b�v���x�����܂��B
echo �v���W�F�N�g�̃��[�g�f�B���N�g��������s����邱�Ƃ�O��Ƃ��Ă��܂��B
echo(
echo [+] �����Z�b�g�A�b�v���J�n���܂�...
echo(

REM --- Check for Python and Pip ---
echo [+] Python �� Pip ���m�F���Ă��܂�...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] �G���[: Python ���C���X�g�[������Ă��Ȃ����A�V�X�e���� PATH �Ɍ�����܂���B
    echo     Python 3.11 ^(https://www.python.org/^ ����^) ���C���X�g�[�����Ă��������B
    echo     �C���X�g�[������ PATH �ɒǉ�����Ă��邱�Ƃ��m�F���Ă��������B
    goto :eof_final
)

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] �G���[: Pip ���C���X�g�[������Ă��܂���BPython ���������C���X�g�[������Ă���΁A����͒ʏ픭�����܂���B
    echo     Python �̃C���X�g�[���� Pip ���܂܂�Ă��邱�Ƃ��m�F���Ă��������B
    goto :eof_final
)
echo     Python �� Pip ��������܂����B
echo(

REM --- Create and Activate Virtual Environment ---
REM Create Virtual Environment
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [+] ���z���� "%VENV_DIR%" �ɍ쐬���Ă��܂�...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [!] �G���[: ���z���̍쐬�Ɏ��s���܂����B
        goto :eof_final
    )
    echo     ���z��������ɍ쐬����܂����B
) else (
    echo [+] ���z���� "%VENV_DIR%" �Ɋ��ɑ��݂��܂��B
)
echo(
echo [+] �Z�b�g�A�b�v�̂��߂ɉ��z�����A�N�e�B�x�[�g���Ă��܂�...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] �G���[: ���z���̃A�N�e�B�x�[�g�Ɏ��s���܂����B
    goto :eof_final
)
echo     ���z�����A�N�e�B�x�[�g����܂����B
echo(

REM --- Install Dependencies (during initial setup) ---
echo [+] �ˑ��֌W�t�@�C�� "%REQUIREMENTS_FILE%" �̑��݂��m�F���Ă��܂�...
if not exist "%REQUIREMENTS_FILE%" (
    echo [!] �G���[: �ˑ��֌W�t�@�C����������܂���: "%REQUIREMENTS_FILE%"
    echo     �v���W�F�N�g�� "%IMAGE_DIR%" �t�H���_���� "requirements.txt" �����������O�ő��݂��邩�m�F���Ă��������B
    echo     ���݂̃X�N���v�g�̏ꏊ ^(�J�����g�f�B���N�g��^): "%CD%"
    goto :deactivate_venv_after_setup_error
)
echo     �ˑ��֌W�t�@�C����������܂����B
echo [+] "%REQUIREMENTS_FILE%" ����ˑ��֌W���C���X�g�[�����Ă��܂�...
python -m pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo [!] �G���[: �ˑ��֌W�̃C���X�g�[���Ɏ��s���܂����B��L�̃G���[���b�Z�[�W���m�F���Ă��������B
    echo     ����: ���̃v���W�F�N�g�̓f�t�H���g�� SQLite ���g�p����悤�ɐݒ肳��Ă��܂��B
    echo     %REQUIREMENTS_FILE% �ɏ]���āAPostgreSQL�p�̈ˑ��֌W 'psycopg2' ���C���X�g�[������܂��B
    echo     'psycopg2' �Ɋ֘A����G���[�̏ꍇ:
    echo     1. PostgreSQL �N���C�A���g���C�u�������C���X�g�[������APATH �Ɋ܂܂�Ă��邱�Ƃ��m�F���Ă��������B
    echo        ��� SQLite ���g�p����\��ł��A'psycopg2' ���ˑ��֌W�Ƃ��Ċ܂܂�Ă��邽�ߕK�v�ł��B
    echo     2. Microsoft Visual C++ Build Tools ���K�v�ɂȂ�ꍇ������܂��B
    echo     3. 'psycopg2' �̃C���X�g�[����e�Ղɂ��邽�߂ɁA�蓮�ŕҏW���邱�Ƃ������ł��܂�
    echo        "%REQUIREMENTS_FILE%" �� 'psycopg2' �� 'psycopg2-binary' �ɕύX���A
    echo        ���̌�A���̃X�N���v�g���Ď��s���邩�A�蓮�� 'pip install -r "%REQUIREMENTS_FILE%"' �����s���Ă��������B
    echo     �����Z�b�g�A�b�v�ɂ́A'psycopg2' ���܂ނ��ׂĂ̈ˑ��֌W�̐���ȃC���X�g�[�����K�v�ł��B
    goto :deactivate_venv_after_setup_error
) else (
    echo     �ˑ��֌W������ɃC���X�g�[������܂����B^(�I�v�V������ PostgreSQL �g�p�̂��߂� 'psycopg2' ���܂݂܂�^)
)
echo(

REM --- .env File Setup (during initial setup) ---
echo [+] %ENV_FILE% �� .env �t�@�C�����m�F���Ă��܂�...
echo DEBUG: Point A - Just after echoing ENV_FILE check.
echo DEBUG: SCR_DIR is [%SCR_DIR%]
REM �������ݐ�f�B���N�g�����Ȃ���΍쐬
if not exist "%SCR_DIR%" (
    echo DEBUG: Point B - SCR_DIR does not exist.
    echo [+] �f�B���N�g�� "%SCR_DIR%" ���쐬���Ă��܂�...
    mkdir "%SCR_DIR%"
)
echo DEBUG: Point C - After SCR_DIR check/creation. ENV_FILE is [%ENV_FILE%]
REM Reset errorlevel before the next IF statement as a precaution
(call )
echo DEBUG: Point D - Before checking if ENV_FILE exists.

REM --- Check if .env file exists and branch accordingly ---
if exist "%ENV_FILE%" GOTO :handle_env_file_exists

REM --- .env file does NOT exist ---
    echo DEBUG: Point E - ENV_FILE does not exist. Starting .env creation block.
    REM This is the block for when .env does NOT exist
    echo [!] %ENV_FILE% ��������܂���B
    echo     �f�t�H���g�� .env �t�@�C�� ^(SQLite �p�ɐݒ�ς�^) �� "%ENV_FILE%" �ɍ쐬����܂��B
    echo     ��ӂ� SECRET_KEY �������I�ɐ�������܂��B
    echo     �������ꂽ�t�@�C�����̑��̐ݒ���m�F���Ă��������B
    echo(
    REM --- SECRET_KEY �̐��� ---
    echo     �V���� SECRET_KEY �𐶐����Ă��܂�...
    set "SECRET_KEY_TEMP_LINE_FILE=%TEMP%\secret_key_line.txt"
    set "SECRET_KEY_ERROR_FILE=%TEMP%\secret_key_error.txt"

    REM Python script now prints "SECRET_KEY=value" directly to the temp file
    "%VENV_DIR%\Scripts\python.exe" -c "from django.core.management.utils import get_random_secret_key; print(f'SECRET_KEY={get_random_secret_key()}')" > "%SECRET_KEY_TEMP_LINE_FILE%" 2> "%SECRET_KEY_ERROR_FILE%"
    set "PY_ERRORLEVEL=%errorlevel%"
    echo     �f�o�b�O: Python�R�}���h��errorlevel: %PY_ERRORLEVEL%

    if exist "%SECRET_KEY_ERROR_FILE%" (
        echo     �f�o�b�O: Python�G���[�o�̓t�@�C�� "%SECRET_KEY_ERROR_FILE%" �̓��e:
        type "%SECRET_KEY_ERROR_FILE%"
        del "%SECRET_KEY_ERROR_FILE%"
    )

    set "line_not_empty="
    if %PY_ERRORLEVEL% equ 0 (
        if exist "%SECRET_KEY_TEMP_LINE_FILE%" (
            REM Check if the temp file is not empty
            for /F "usebackq" %%A in ("%SECRET_KEY_TEMP_LINE_FILE%") do set "line_not_empty=1"
            if defined line_not_empty (
                echo     SECRET_KEY ������ɐ�������܂����B
                copy /Y "%SECRET_KEY_TEMP_LINE_FILE%" "%ENV_FILE%" > nul
                GOTO :secret_key_written_to_env
            ) else (
                echo     �f�o�b�O: Python�͐������܂������A�o�̓t�@�C�� "%SECRET_KEY_TEMP_LINE_FILE%" ����ł��B
            )
        ) else (
            echo     �f�o�b�O: Python�͐������܂������A�o�̓t�@�C�� "%SECRET_KEY_TEMP_LINE_FILE%" ��������܂���B
        )
    )

    REM Fallthrough to here means SECRET_KEY generation failed
:handle_secret_key_generation_failure
        echo [!] �x��: SECRET_KEY �̎��������Ɏ��s���܂����B
        echo            Django ���܂��C���X�g�[������Ă��Ȃ����APython �X�N���v�g���s���ɃG���[�����������\��������܂��B
        echo            �v���[�X�z���_�[�L�[���g�p����܂��B"%ENV_FILE%" �Ŏ蓮�ŕύX����K�v������܂��B
        (echo SECRET_KEY=your_very_secret_and_unique_django_key_here_please_change_me_manually_!!!) > "%ENV_FILE%"

:secret_key_written_to_env
    if exist "%SECRET_KEY_TEMP_LINE_FILE%" del "%SECRET_KEY_TEMP_LINE_FILE%"
    echo(

    REM Append other settings to .env file
    echo DEBUG=True >> "%ENV_FILE%"
    echo ALLOWED_HOSTS=* >> "%ENV_FILE%"
    echo CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000 >> "%ENV_FILE%"
    echo DB_ENGINE=django.db.backends.sqlite3 >> "%ENV_FILE%"
    echo DB_NAME=db.sqlite3 >> "%ENV_FILE%"
    echo     �f�t�H���g�� .env �t�@�C�� ^(SQLite �p�ɐݒ�ς�^) �� "%ENV_FILE%" �ɍ쐬����܂����B
    echo(
    echo     ========================= �d�v: �Ή����K�v�ł� =========================
    echo     1. �V�����쐬���ꂽ "%ENV_FILE%" ���m�F���Ă��������B��ӂ� SECRET_KEY ��
    echo        �����I�ɐ�������܂����B�����Ɏ��s�����ꍇ�́A�蓮�Őݒ肷��K�v������܂��B
    echo     2. ALLOWED_HOSTS ��f�[�^�x�[�X�ݒ�ȂǁA���̐ݒ���m�F���Ă��������B    
    echo     3. �f�t�H���g�̃f�[�^�x�[�X�� SQLite �ł� ^("%ENV_FILE%" �Ŏ��O�ݒ�ς�^)�B
    echo        SQLite �f�[�^�x�[�X�t�@�C�� ^(��: �f�t�H���g�� .env �ɏ]�� db.sqlite3^) �́A
    echo        ���݂��Ȃ��ꍇ�A�}�C�O���[�V�������� Django �ɂ���Ď����I�ɍ쐬����܂��B
    echo     4. ����� PostgreSQL ���g�p����ꍇ�́A"%ENV_FILE%" ��ҏW���A
    echo        PostgreSQL �T�[�o�[�̏ڍׂ���͂��A���s����Ă��邱�Ƃ��m�F����K�v������܂��B
    echo     ===========================================================================
    echo(
    pause    
    GOTO :after_env_file_handling

:handle_env_file_exists
    REM This is the block for when .env DOES exist
    echo DEBUG: Point F - ENV_FILE exists.
    echo     %ENV_FILE% ��������܂����B�������ݒ肳��Ă��邱�Ƃ��m�F���Ă��������B
    echo     SQLite ^(�f�t�H���g^) �̏ꍇ: DB_ENGINE=django.db.backends.sqlite3, DB_NAME=db.sqlite3
    echo     �����āA��ӂ� SECRET_KEY ���ݒ肳��Ă��邱�Ƃ��m�F���Ă��������B
    echo     PostgreSQL ���g�p����ꍇ�́A�ڑ��ڍׂ����������Ƃ��m�F���Ă��������B
    GOTO :after_env_file_handling

:after_env_file_handling
echo(
REM --- Database Setup Reminder (during initial setup) ---
echo =====================================
echo  �f�[�^�x�[�X�ݒ�
echo =====================================
echo ���̃v���W�F�N�g�̓f�t�H���g�� SQLite ���g�p����悤�ɐݒ肳��Ă��܂��B
echo 1. "%ENV_FILE%" �Ɉ�ӂ� SECRET_KEY ���ݒ肳��Ă��邱�Ƃ��m�F���Ă��������B
echo 2. SQLite �f�[�^�x�[�X (��: �f�t�H���g�� .env �ɏ]�� 'db.sqlite3') �́A
echo    ���݂��Ȃ��ꍇ�A�}�C�O���[�V�������� Django �ɂ���Ď����I�ɍ쐬����܂��B
echo    DB_ENGINE �� 'django.db.backends.sqlite3' �ł���ADB_NAME �� "%ENV_FILE%" �ɐݒ肳��Ă��邱�Ƃ��m�F���Ă��������B
echo.
echo ����� PostgreSQL ���g�p���邱�Ƃ�I�������ꍇ ("%ENV_FILE%" ��ύX�����ꍇ):
echo 1. PostgreSQL �T�[�o�[���C���X�g�[������A���s����Ă��邱�Ƃ��m�F���Ă��������B
echo 2. �K�v�Ȍ��������f�[�^�x�[�X�ƃ��[�U�[���쐬�ς݂ł��邱�Ƃ��m�F���Ă��������B
echo 3. "%ENV_FILE%" �������� PostgreSQL �ڑ��ڍׂōX�V����Ă��邱�Ƃ��m�F���Ă�������
echo    (DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)�B
echo.
echo PostgreSQL �T�|�[�g�p�� 'psycopg2' ���C�u�����͈ˑ��֌W�Ɋ܂܂�Ă���A
echo �C���X�g�[������Ă���͂��ł��B
echo.
echo �f�[�^�x�[�X�� .env �t�@�C�����������ݒ肳��Ă��邱�Ƃ��m�F������A�����L�[�������đ��s���Ă�������...
pause
echo(

REM --- Run Django Migrations (during initial setup) ---
echo [+] Django �}�C�O���[�V���������s���Ă��܂� (�����Z�b�g�A�b�v)...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] �G���[: �����Z�b�g�A�b�v���̃}�C�O���[�V�����̎��s�Ɏ��s���܂����B
    echo     "%ENV_FILE%" �̃f�[�^�x�[�X�ݒ���m�F���Ă��������B
    echo     - SQLite ^(�f�t�H���g^) �̏ꍇ: DB_ENGINE='django.db.backends.sqlite3' �ł���ADB_NAME ���w�肳��Ă��邱�Ƃ��m�F���Ă��������B
    echo       �X�N���v�g�́ASQLite �t�@�C�������݂��Ȃ��ꍇ�ɍ쐬�����݂܂��B
    echo       ���s�����ꍇ�́A�v���W�F�N�g�f�B���N�g���̏������݌������m�F���Ă��������B
    echo     - PostgreSQL �̏ꍇ: �T�[�o�[�����s���ŃA�N�Z�X�\�ł���A�f�[�^�x�[�X/���[�U�[�����݂��A
    echo       "%ENV_FILE%" �̔F�؏�񂪐��������Ƃ��m�F���Ă��������B
    goto :deactivate_venv_after_setup_error
)
echo     �����}�C�O���[�V����������Ɋ������܂����B
echo(

REM --- Create Superuser (Optional but Recommended, during initial setup) ---
echo [+] ���O��`���ꂽ�p�X���[�h�ŃX�[�p�[���[�U�[ 'admin' ���쐬���Ă��܂�...

REM Set environment variables for non-interactive superuser creation
set "DJANGO_SUPERUSER_USERNAME=admin"
set "DJANGO_SUPERUSER_PASSWORD=admin"

python "%MANAGE_PY%" createsuperuser --noinput
if %errorlevel% neq 0 (
    echo [!] �x��: �X�[�p�[���[�U�[ 'admin' �̎����쐬�Ɏ��s���܂����B
    echo     ����́A���[�U�[�����ɑ��݂���ꍇ��A�ʂ̃G���[�����������ꍇ�ɋN����\��������܂��B
    echo     �蓮�ō쐬����K�v�����邩������܂���: python manage.py createsuperuser
) else (
    echo     �X�[�p�[���[�U�[ 'admin' ������ɍ쐬���ꂽ���A���ɑ��݂��܂��B
)
set "DJANGO_SUPERUSER_USERNAME="
set "DJANGO_SUPERUSER_PASSWORD="
echo(

REM --- Mark setup as complete ---
echo [+] �����Z�b�g�A�b�v�v���Z�X���������܂����B
echo [+] �Z�b�g�A�b�v�����t���O���쐬���Ă��܂�: "%SETUP_COMPLETE_FLAG_FILE%"
echo.> "%SETUP_COMPLETE_FLAG_FILE%"
if %errorlevel% neq 0 (
    echo [!] �G���[: �Z�b�g�A�b�v�����t���O�̍쐬�Ɏ��s���܂����B
    echo     ����A�A�v���P�[�V�������ēx�����Z�b�g�A�b�v�����s����\��������܂��B
    goto :deactivate_venv_after_setup_error
)
echo     �Z�b�g�A�b�v�����t���O���쐬����܂����B
echo(
echo [+] �A�v���P�[�V�����̋N���ɐi�݂܂�...
echo(
REM Fall through to :run_application

:run_application
REM This label is for subsequent runs or after initial setup completes.

REM --- Activate Virtual Environment (for running application) ---
echo [+] ���z�����A�N�e�B�x�[�g���Ă��܂�...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] �G���[: ���z���̃A�N�e�B�x�[�g�Ɏ��s���܂����B
    goto :eof_final
)
echo     ���z�����A�N�e�B�x�[�g����܂����B
echo(

REM --- Run Django Migrations (always run before server start) ---
echo [+] Django �}�C�O���[�V���������s���Ă��܂�...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] �G���[: �}�C�O���[�V�����̎��s�Ɏ��s���܂����B
    echo     "%ENV_FILE%" �̃f�[�^�x�[�X�ݒ���m�F���Ă��������B
    echo     - SQLite ^(�f�t�H���g^) �̏ꍇ: DB_ENGINE='django.db.backends.sqlite3' �ł���ADB_NAME ���w�肳��Ă��邱�Ƃ��m�F���Ă��������B
    echo       �X�N���v�g�́ASQLite �t�@�C�������݂��Ȃ��ꍇ�ɍ쐬�����݂܂��B
    echo       ���s�����ꍇ�́A�v���W�F�N�g�f�B���N�g���̏������݌������m�F���Ă��������B
    echo     - PostgreSQL �̏ꍇ: �T�[�o�[�����s���ŃA�N�Z�X�\�ł���A�f�[�^�x�[�X/���[�U�[�����݂��A
    echo       "%ENV_FILE%" �̔F�؏�񂪐��������Ƃ��m�F���Ă��������B
    goto :deactivate_venv_and_exit
)
echo     �}�C�O���[�V����������Ɋ������܂����B
echo(

REM --- Start Development Server ---
echo [+] Django �J���T�[�o�[���N�����Ă��܂�...
echo     �A�v���P�[�V�����ɂ� http://127.0.0.1:8000 �ŃA�N�Z�X�ł���͂��ł��B
echo     �T�[�o�[���~����ɂ́A���̃E�B���h�E�� Ctrl+C �������Ă��������B
echo(
python "%MANAGE_PY%" runserver 0.0.0.0:8000

echo �T�[�o�[����~���܂����B

:deactivate_venv_and_exit
echo [+] ���z�����A�N�e�B�u�����Ă��܂�...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:deactivate_venv_after_setup_error
echo [+] �Z�b�g�A�b�v�G���[��A���z�����A�N�e�B�u�����Ă��܂�...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:eof_final
echo(
echo �Z�b�g�A�b�v�X�N���v�g���I�����܂����B
REM pushd �ŕύX�����J�����g�f�B���N�g�������ɖ߂�
popd
pause
endlocal
