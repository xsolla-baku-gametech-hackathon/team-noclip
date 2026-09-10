/*
 * Xsolla Game Recap - Native Windows C++ Launcher
 * Compiles to a zero-console, ultra-fast native Windows executable.
 * Launches the Xsolla Game Recap overlay seamlessly in the background.
 */

#include <windows.h>
#include <string>
#include <vector>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Get the directory of this executable
    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);
    std::string currentDir(exePath);
    size_t lastSlash = currentDir.find_last_of("\\/");
    if (lastSlash != std::string::npos) {
        currentDir = currentDir.substr(0, lastSlash);
    }

    // Priority: pythonw for 100% silent zero-console execution
    std::string cmd = "pythonw main.py " + std::string(lpCmdLine);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE; // Run completely hidden
    ZeroMemory(&pi, sizeof(pi));

    std::vector<char> cmdVec(cmd.begin(), cmd.end());
    cmdVec.push_back('\0');

    BOOL success = CreateProcessA(
        NULL,
        cmdVec.data(),
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW | DETACHED_PROCESS,
        NULL,
        currentDir.c_str(),
        &si,
        &pi
    );

    if (!success) {
        // Fallback: try python with hidden window
        std::string fallbackCmd = "python main.py " + std::string(lpCmdLine);
        std::vector<char> fbVec(fallbackCmd.begin(), fallbackCmd.end());
        fbVec.push_back('\0');

        success = CreateProcessA(
            NULL,
            fbVec.data(),
            NULL,
            NULL,
            FALSE,
            CREATE_NO_WINDOW,
            NULL,
            currentDir.c_str(),
            &si,
            &pi
        );
    }

    if (!success) {
        MessageBoxA(
            NULL,
            "Failed to launch Xsolla Game Recap.\nPlease make sure Python is installed and in your system PATH.",
            "Xsolla Game Recap - Launcher Error",
            MB_ICONERROR | MB_OK
        );
        return 1;
    }

    // Process launched successfully!
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return 0;
}
