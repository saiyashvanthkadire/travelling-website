$dir = 'c:\Users\YashvanthReddy\OneDrive\Desktop\projects\Aeroquest\template'
$files = @('homepage.html','destination.html','packages.html','contact.html','Bookingform.html')

$mobileCSS = @'

    /* ── Mobile navbar toggle button ── */
    .menu-toggle {
      display: none;
      width: 40px; height: 40px;
      border: 1px solid rgba(255,255,255,0.22);
      border-radius: 10px;
      background: rgba(255,255,255,0.12);
      color: #fff; cursor: pointer;
      align-items: center; justify-content: center;
      flex-direction: column; gap: 5px; flex-shrink: 0;
    }
    .menu-toggle span {
      width: 20px; height: 2px; border-radius: 999px;
      background: currentColor;
      transition: transform 0.25s ease, opacity 0.25s ease;
    }
    .menu-toggle.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .menu-toggle.open span:nth-child(2) { opacity: 0; }
    .menu-toggle.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

    /* ── Mobile layout: hamburger | logo | user icon ── */
    @media (max-width: 768px) {
      header, .header {
        display: grid !important;
        grid-template-columns: 44px 1fr 44px !important;
        grid-template-rows: auto auto !important;
        align-items: center !important;
        padding: 12px 16px !important;
        gap: 0 8px !important;
      }
      .menu-toggle {
        display: inline-flex !important;
        grid-column: 1; grid-row: 1;
      }
      .nav-logo-center {
        grid-column: 2; grid-row: 1;
        display: flex !important;
        justify-content: center;
        align-items: center;
      }
      .nav-user-right {
        grid-column: 3; grid-row: 1;
        display: flex !important;
        justify-content: flex-end;
        align-items: center;
      }
      nav {
        display: none !important;
        grid-column: 1 / -1; grid-row: 2;
        flex-direction: column;
        align-items: stretch;
        gap: 6px; padding: 10px;
        border-radius: 14px;
        background: rgba(8,27,51,0.96);
        margin-top: 8px; width: 100%;
      }
      nav.open { display: flex !important; }
      nav a { padding: 10px 12px; border-radius: 10px; }
      nav a:hover, nav a.active { background: rgba(255,255,255,0.12); }
      nav .user-menu { display: none !important; }
      .brand-tag { display: none !important; }
      .logo-icon { width: 42px !important; height: 42px !important; }
      .logo-text strong { font-size: 17px !important; }
      .logo-text span { font-size: 9px !important; }
    }
'@

$toggleBtn = '<button class="menu-toggle" type="button" aria-label="Toggle navigation" aria-expanded="false"><span></span><span></span><span></span></button>'

$navScript = @'
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('nav');
    if (menuToggle && navMenu) {
      menuToggle.addEventListener('click', () => {
        const isOpen = navMenu.classList.toggle('open');
        menuToggle.classList.toggle('open', isOpen);
        menuToggle.setAttribute('aria-expanded', String(isOpen));
      });
      navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          navMenu.classList.remove('open');
          menuToggle.classList.remove('open');
          menuToggle.setAttribute('aria-expanded', 'false');
        });
      });
    }
    const savedName = localStorage.getItem('aeroquestUserName');
    const savedEmail = localStorage.getItem('aeroquestUserEmail');
    const initial = savedName ? savedName.trim().charAt(0).toUpperCase() : (savedEmail ? savedEmail.trim().charAt(0).toUpperCase() : '');
    document.querySelectorAll('.user-initial').forEach(el => {
      if (savedEmail) { el.textContent = initial; el.title = savedName || savedEmail; el.classList.add('show'); }
    });
    document.querySelectorAll('.user-initial').forEach(btn => {
      const dd = btn.nextElementSibling;
      if (!dd) return;
      btn.addEventListener('click', e => {
        e.stopPropagation();
        document.querySelectorAll('.user-dropdown').forEach(d => { if (d !== dd) d.classList.remove('show'); });
        dd.classList.toggle('show');
      });
    });
    document.addEventListener('click', () => document.querySelectorAll('.user-dropdown').forEach(d => d.classList.remove('show')));
'@

foreach ($f in $files) {
    $path = Join-Path $dir $f
    $c = [System.IO.File]::ReadAllText($path)

    # 1. Inject mobile CSS before closing </style>
    $c = $c.Replace('  </style>', ($mobileCSS + '  </style>'))

    # 2. For files using brand-group: wrap logo in nav-logo-center, add toggle btn before it, add nav-user-right after brand-group closing
    if ($c.Contains('class="brand-group"')) {
        # Add toggle button + open nav-logo-center before brand-group
        $c = $c.Replace('<div class="brand-group">', ($toggleBtn + '<div class="nav-logo-center"><div class="brand-group">'))
        # Close nav-logo-center after brand-group's closing div (before <nav)
        # brand-group closes with </div> then whitespace then <nav
        $c = [regex]::Replace($c, '(</div>\s*)([\r\n]+\s*<nav)', {
            param($m)
            $m.Groups[1].Value + '</div>' + '<div class="nav-user-right"><div class="user-menu"><button class="user-initial" type="button" aria-label="Open account menu"></button><div class="user-dropdown"><button type="button" class="settings-btn">Settings</button><button type="button" class="logout-btn">Logout</button></div></div></div>' + $m.Groups[2].Value
        }, 1)
    }
    # For homepage.html which uses a plain <div> wrapping logo (no brand-group class)
    elseif ($c.Contains('class="logo-mark"') -and -not $c.Contains('class="brand-group"')) {
        # Find the outer <div> before logo-mark and wrap
        $c = [regex]::Replace($c, '(<header[^>]*>[\r\n\s]+)(<div>)', {
            param($m)
            $m.Groups[1].Value + $toggleBtn + '<div class="nav-logo-center"><div>'
        }, 1)
        $c = [regex]::Replace($c, '(</div>\s*)([\r\n]+\s*<nav)', {
            param($m)
            $m.Groups[1].Value + '</div>' + '<div class="nav-user-right"><div class="user-menu"><button class="user-initial" type="button" aria-label="Open account menu"></button><div class="user-dropdown"><button type="button" class="settings-btn">Settings</button><button type="button" class="logout-btn">Logout</button></div></div></div>' + $m.Groups[2].Value
        }, 1)
    }

    # 3. Replace old script block with new unified one
    $oldScript1 = 'const savedEmail = localStorage.getItem("aeroquestUserEmail");
    const userInitial = document.querySelector(".user-initial");

    if (savedEmail && userInitial) {
      userInitial.textContent = savedEmail.trim().charAt(0);
      userInitial.title = savedEmail;
      userInitial.classList.add("show");
    }

    const userMenuButton = document.querySelector(".user-initial");
    const userDropdown = document.querySelector(".user-dropdown");'

    if ($c.Contains($oldScript1)) {
        $c = $c.Replace($oldScript1, $navScript + '
    const userMenuButton = document.querySelector(".user-initial");
    const userDropdown = document.querySelector(".user-dropdown");')
    }

    [System.IO.File]::WriteAllText($path, $c)
    Write-Host "Done: $f"
}
Write-Host "All files updated."
