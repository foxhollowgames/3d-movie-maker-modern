#ifndef DISPLAYSETTINGSWIN_H
#define DISPLAYSETTINGSWIN_H

#include "displaysettings.h"
#include "utestres.h"

namespace DisplaySettings
{
constexpr UINT MenuCommand = 0xE100;

inline void AddMenu(HWND window)
{
    HMENU menu = GetSystemMenu(window, FALSE);
    if (menu && GetMenuState(menu, MenuCommand, MF_BYCOMMAND) == UINT(-1))
    {
        AppendMenu(menu, MF_SEPARATOR, 0, nullptr);
        AppendMenuA(menu, MF_STRING, MenuCommand, "Display Settings...\tF11");
    }
}

inline MONITORINFO CurrentMonitor(HWND window)
{
    MONITORINFO monitor = {};
    monitor.cbSize = sizeof(monitor);
    if (!GetMonitorInfo(MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST), &monitor))
    {
        SetRect(&monitor.rcMonitor, 0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));
        monitor.rcWork = monitor.rcMonitor;
        SystemParametersInfo(SPI_GETWORKAREA, 0, &monitor.rcWork, 0);
    }
    return monitor;
}

struct DialogState
{
    bool fullscreen;
    int width, height;
    MONITORINFO monitor;
};

inline void UpdatePreview(HWND dialog, DialogState *state)
{
    bool fullscreen = IsDlgButtonChecked(dialog, IDC_DISPLAY_FULLSCREEN) == BST_CHECKED;
    EnableWindow(GetDlgItem(dialog, IDC_DISPLAY_SIZE), !fullscreen);
    char text[256];
    if (fullscreen)
    {
        wsprintfA(text, "Full screen: %d x %d pixels. The desktop resolution stays unchanged.",
                  state->monitor.rcMonitor.right - state->monitor.rcMonitor.left,
                  state->monitor.rcMonitor.bottom - state->monitor.rcMonitor.top);
    }
    else
    {
        int selected = int(SendDlgItemMessage(dialog, IDC_DISPLAY_SIZE, CB_GETCURSEL, 0, 0));
        Size requested =
            selected >= 0 && selected < PresetCount ? Presets[selected] : Size{state->width, state->height};
        RECT border = {};
        AdjustWindowRect(&border, WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN, FALSE);
        auto size = FitWindow(requested.width, requested.height,
                              state->monitor.rcWork.right - state->monitor.rcWork.left - (border.right - border.left),
                              state->monitor.rcWork.bottom - state->monitor.rcWork.top - (border.bottom - border.top));
        wsprintfA(text, "Window picture area: %d x %d pixels. Large sizes are reduced to fit this display.", size.width,
                  size.height);
    }
    SetDlgItemTextA(dialog, IDC_DISPLAY_PREVIEW, text);
}

inline INT_PTR CALLBACK DialogProc(HWND dialog, UINT message, WPARAM wParam, LPARAM lParam)
{
    auto state = reinterpret_cast<DialogState *>(GetWindowLongPtr(dialog, GWLP_USERDATA));
    if (message == WM_INITDIALOG)
    {
        state = reinterpret_cast<DialogState *>(lParam);
        SetWindowLongPtr(dialog, GWLP_USERDATA, lParam);
        char text[256];
        wsprintfA(text, "Detected display: %d x %d pixels. Full screen automatically follows this display.",
                  state->monitor.rcMonitor.right - state->monitor.rcMonitor.left,
                  state->monitor.rcMonitor.bottom - state->monitor.rcMonitor.top);
        SetDlgItemTextA(dialog, IDC_DISPLAY_DETECTED, text);
        int selected = 0;
        for (int i = 0; i < PresetCount; ++i)
        {
            if (i == 0)
                lstrcpyA(text, "Automatic (fit display)");
            else
                wsprintfA(text, "%d x %d", Presets[i].width, Presets[i].height);
            SendDlgItemMessageA(dialog, IDC_DISPLAY_SIZE, CB_ADDSTRING, 0, reinterpret_cast<LPARAM>(text));
            if (state->width == Presets[i].width && state->height == Presets[i].height)
                selected = i;
        }
        if (selected == 0 && ValidSize(state->width, state->height))
        {
            wsprintfA(text, "%d x %d (custom)", state->width, state->height);
            SendDlgItemMessageA(dialog, IDC_DISPLAY_SIZE, CB_ADDSTRING, 0, reinterpret_cast<LPARAM>(text));
            selected = PresetCount;
        }
        SendDlgItemMessage(dialog, IDC_DISPLAY_SIZE, CB_SETCURSEL, selected, 0);
        CheckRadioButton(dialog, IDC_DISPLAY_FULLSCREEN, IDC_DISPLAY_WINDOWED,
                         state->fullscreen ? IDC_DISPLAY_FULLSCREEN : IDC_DISPLAY_WINDOWED);
        UpdatePreview(dialog, state);
        return TRUE;
    }
    if (message == WM_COMMAND && state)
    {
        switch (LOWORD(wParam))
        {
        case IDOK: {
            state->fullscreen = IsDlgButtonChecked(dialog, IDC_DISPLAY_FULLSCREEN) == BST_CHECKED;
            int selected = int(SendDlgItemMessage(dialog, IDC_DISPLAY_SIZE, CB_GETCURSEL, 0, 0));
            if (selected >= 0 && selected < PresetCount)
            {
                state->width = Presets[selected].width;
                state->height = Presets[selected].height;
            }
            EndDialog(dialog, IDOK);
            return TRUE;
        }
        case IDCANCEL:
            EndDialog(dialog, IDCANCEL);
            return TRUE;
        case IDC_DISPLAY_RESET:
            CheckRadioButton(dialog, IDC_DISPLAY_FULLSCREEN, IDC_DISPLAY_WINDOWED, IDC_DISPLAY_FULLSCREEN);
            SendDlgItemMessage(dialog, IDC_DISPLAY_SIZE, CB_SETCURSEL, 0, 0);
            UpdatePreview(dialog, state);
            return TRUE;
        case IDC_DISPLAY_FULLSCREEN:
        case IDC_DISPLAY_WINDOWED:
        case IDC_DISPLAY_SIZE:
            UpdatePreview(dialog, state);
            return TRUE;
        }
    }
    return FALSE;
}
} // namespace DisplaySettings
#endif
