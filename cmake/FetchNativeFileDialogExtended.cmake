include(FetchContent)

FetchContent_Declare(
    nativefiledialog-extended
    GIT_REPOSITORY https://github.com/btzy/nativefiledialog-extended
    GIT_TAG 65b2f070a0fcfee0d453a64e770a217ab0b6ff4f
)

FetchContent_MakeAvailable(
    nativefiledialog-extended
)
