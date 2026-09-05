<#
.SYNOPSIS
    hwpx 스킬을 Claude Code / Codex CLI에 설치합니다. (Windows PowerShell)

.DESCRIPTION
    저장소의 skills/hwpx 폴더를 각 도구가 읽는 위치로 복사합니다.
    파일을 덮어쓰기만 하며, 기존 폴더를 지우지 않습니다.

.PARAMETER Target
    all    - Claude Code + Codex 모두 (기본값)
    claude - Claude Code 개인 스킬 폴더에만
    codex  - Codex CLI 개인 스킬 폴더에만

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Target codex
#>

param(
    [ValidateSet('all', 'claude', 'codex')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'

# 이 스크립트가 있는 폴더 = 저장소 루트
$RepoRoot  = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc  = Join-Path $RepoRoot 'skills\hwpx'

if (-not (Test-Path $SkillSrc)) {
    Write-Error "스킬 폴더를 찾을 수 없습니다: $SkillSrc"
    exit 1
}

function Install-Skill {
    param([string]$DestRoot, [string]$Label)

    $Dest = Join-Path $DestRoot 'hwpx'
    New-Item -ItemType Directory -Force -Path $DestRoot | Out-Null

    if (Test-Path $Dest) {
        Write-Host "  기존 설치를 덮어씁니다: $Dest" -ForegroundColor DarkYellow
    }

    Copy-Item -Path $SkillSrc -Destination $DestRoot -Recurse -Force
    $count = (Get-ChildItem -Path $Dest -Recurse -File).Count
    Write-Host "  [OK] $Label -> $Dest ($count개 파일)" -ForegroundColor Green
}

Write-Host ""
Write-Host "hwpx 스킬 설치" -ForegroundColor Cyan
Write-Host "----------------------------------------"

if ($Target -eq 'all' -or $Target -eq 'claude') {
    Install-Skill -DestRoot (Join-Path $HOME '.claude\skills') -Label 'Claude Code'
}

if ($Target -eq 'all' -or $Target -eq 'codex') {
    Install-Skill -DestRoot (Join-Path $HOME '.agents\skills') -Label 'Codex CLI'
}

Write-Host "----------------------------------------"
Write-Host ""
Write-Host "다음 단계" -ForegroundColor Cyan
Write-Host "  1) 의존 패키지 설치 (한 번만)"
Write-Host "       pip install python-hwpx"
Write-Host "  2) 도구를 재시작한 뒤 이렇게 요청해 보세요"
Write-Host "       \"이 내용으로 한글 문서 만들어줘\""
Write-Host ""
Write-Host "  Cowork(클로드 데스크톱 앱)에서 쓰려면 이 스크립트가 아니라"
Write-Host "  dist\hwpx-v1.4.1.skill 파일을 대화창에 올려 저장하세요."
Write-Host ""
