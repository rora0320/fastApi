set -ex

CURRENT_DIR=$(pwd)

echo "CURRENT_DIR: $CURRENT_DIR"
BASE_DIR="$CURRENT_DIR/manual"
BUILD_SCRIPT="$BASE_DIR/build.sh"
BUILD_DIR="$BASE_DIR/build"

# 빌드 스크립트 있는지 확인
if [ -f "$BUILD_SCRIPT" ]; then
    echo "Found '$BUILD_SCRIPT' file"

    # 빌드 스크립트가 있는곳으로 이동
    cd "$BASE_DIR" || exit

    # 실행
    sh "$BUILD_SCRIPT"

    # 빌드 폴더 만들어질 때까지 대기
    while [ ! -d "$BUILD_DIR" ]; do
        sleep 5
    done
else
    echo "The file '$BUILD_SCRIPT' does not exist."
    exit 1
fi
