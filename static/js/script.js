/* ==========================================================================
   TASTY HUB — MULTI-PAGE PERSISTENT FRONT-END SCRIPT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {



    // ==========================================
    // 1. DYNAMIC HEADER HEIGHT FOR STICKY OFFSET
    // ==========================================
    const header = document.querySelector('header');

    function updateHeaderHeight() {
        if (header) {
            const h = header.offsetHeight;
            document.documentElement.style.setProperty('--header-height', h + 'px');
        }
    }
    updateHeaderHeight();
    window.addEventListener('resize', updateHeaderHeight, { passive: true });

    // ==========================================
    // 2. SCROLL TRIGGERED STICKY NAVIGATION
    // ==========================================
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scroll-nav');
        } else {
            header.classList.remove('scroll-nav');
        }
        updateHeaderHeight();
    });

    // ==========================================
    // 2.5. NAVIGATION SIDEBAR DRAWER
    // ==========================================
    const openNavSidebarBtn = document.getElementById('openNavSidebarBtn');
    const closeNavSidebarBtn = document.getElementById('closeNavSidebarBtn');
    const navSidebar = document.getElementById('navSidebar');
    const navSidebarOverlay = document.getElementById('navSidebarOverlay');

    function openNavSidebar() {
        if (navSidebar) {
            navSidebar.classList.add('active');
            navSidebar.setAttribute('aria-hidden', 'false');
        }
        if (navSidebarOverlay) navSidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeNavSidebar() {
        if (navSidebar) {
            navSidebar.classList.remove('active');
            navSidebar.setAttribute('aria-hidden', 'true');
        }
        if (navSidebarOverlay) navSidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (openNavSidebarBtn) openNavSidebarBtn.addEventListener('click', openNavSidebar);
    if (closeNavSidebarBtn) closeNavSidebarBtn.addEventListener('click', closeNavSidebar);
    if (navSidebarOverlay) navSidebarOverlay.addEventListener('click', closeNavSidebar);

    if (navSidebar) {
        navSidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeNavSidebar);
        });
    }

    // ==========================================
    // 3. SCROLL REVEAL (INTERSECTION OBSERVER)
    // ==========================================
    const revealElements = document.querySelectorAll('.reveal');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: '0px 0px -50px 0px'
        });

        revealElements.forEach(el => revealObserver.observe(el));
    }

    // ==========================================
    // 4. MOBILE NAVBAR TOGGLE
    // ==========================================
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const navbar = document.getElementById('navbar');

    if (mobileNavToggle && navbar) {
        mobileNavToggle.addEventListener('click', () => {
            navbar.classList.toggle('active');
            const icon = mobileNavToggle.querySelector('i');
            if (navbar.classList.contains('active')) {
                icon.className = 'fa-solid fa-xmark';
            } else {
                icon.className = 'fa-solid fa-bars';
            }
        });

        // Close navbar on click of any nav link
        const navLinks = navbar.querySelectorAll('nav ul li a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navbar.classList.remove('active');
                mobileNavToggle.querySelector('i').className = 'fa-solid fa-bars';
            });
        });
    }

    // ==========================================
    // 5. TESTIMONIALS SLIDER LOGIC (PAGE SPECIFIC)
    // ==========================================
    const slides = document.querySelectorAll('.review-slide');
    const prevBtn = document.getElementById('prevReviewBtn');
    const nextBtn = document.getElementById('nextReviewBtn');
    const indicatorsContainer = document.getElementById('sliderIndicators');
    let currentSlideIndex = 0;
    let sliderTimer = null;

    if (slides.length > 0) {
        const showSlide = (index) => {
            slides.forEach(slide => slide.classList.remove('active'));
            slides[index].classList.add('active');
            
            if (indicatorsContainer) {
                const dots = indicatorsContainer.querySelectorAll('.slider-dot');
                dots.forEach(dot => dot.classList.remove('active'));
                if (dots[index]) dots[index].classList.add('active');
            }
            currentSlideIndex = index;
        };

        const nextSlide = () => {
            let nextIdx = (currentSlideIndex + 1) % slides.length;
            showSlide(nextIdx);
        };

        const prevSlide = () => {
            let prevIdx = (currentSlideIndex - 1 + slides.length) % slides.length;
            showSlide(prevIdx);
        };

        if (nextBtn) nextBtn.addEventListener('click', () => {
            nextSlide();
            resetSliderTimer();
        });

        if (prevBtn) prevBtn.addEventListener('click', () => {
            prevSlide();
            resetSliderTimer();
        });

        if (indicatorsContainer) {
            indicatorsContainer.addEventListener('click', (e) => {
                if (e.target.classList.contains('slider-dot')) {
                    const targetIdx = parseInt(e.target.getAttribute('data-index'), 10);
                    showSlide(targetIdx);
                    resetSliderTimer();
                }
            });
        }

        const startSliderTimer = () => {
            sliderTimer = setInterval(nextSlide, 5000);
        };

        const resetSliderTimer = () => {
            clearInterval(sliderTimer);
            startSliderTimer();
        };

        startSliderTimer();
    }

    // ==========================================
    // 6. MENU CATEGORY FILTER & LIVE SEARCH (PAGE SPECIFIC)
    // ==========================================
    const tabBtns = document.querySelectorAll('.menu-tab-btn');
    const menuGrid = document.getElementById('menuGrid');
    const menuSearchInput = document.getElementById('menuSearchInput');
    const menuSearchBtn = document.getElementById('menuSearchBtn');

    // Custom Mobile Select elements
    const customSelectWrapper = document.getElementById('customMobileSelectWrapper');
    const customSelectTrigger = document.getElementById('customMobileSelectTrigger');
    const customOptionsContainer = document.getElementById('customMobileOptions');
    const menuCarouselDots = document.getElementById('menuCarouselDots');

    if (menuGrid) {
        const menuItems = menuGrid.querySelectorAll('.menu-item-card');
        let activeCategory = 'all';

        // Filter items matching both Category AND Live Search Query
        const applyMenuFilters = () => {
            const searchQuery = menuSearchInput ? menuSearchInput.value.trim().toLowerCase() : '';

            menuItems.forEach(item => {
                const itemCat = item.getAttribute('data-category');
                const titleText = item.querySelector('h4') ? item.querySelector('h4').textContent.toLowerCase() : '';
                const descText = item.querySelector('.menu-item-desc') ? item.querySelector('.menu-item-desc').textContent.toLowerCase() : '';

                const matchesCategory = (activeCategory === 'all' || itemCat === activeCategory);
                const matchesSearch = searchQuery === '' || titleText.includes(searchQuery) || descText.includes(searchQuery);

                if (matchesCategory && matchesSearch) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });

            generateCarouselDots();
        };

        // Live Search Input Listener
        if (menuSearchInput) {
            menuSearchInput.addEventListener('input', () => {
                applyMenuFilters();
            });
        }
        if (menuSearchBtn) {
            menuSearchBtn.addEventListener('click', (e) => {
                e.preventDefault();
                applyMenuFilters();
            });
        }

        // Dynamic Carousel Dots Generator & Updater (Capped at exactly 5 max dots)
        const generateCarouselDots = () => {
            if (!menuCarouselDots) return;
            menuCarouselDots.innerHTML = '';
            
            const visibleCards = Array.from(menuItems).filter(item => item.style.display !== 'none');
            
            const isMobile = window.innerWidth <= 768;
            const gap = isMobile ? 20 : 30;
            const minItemsForDots = isMobile ? 1 : 3;

            if (!isMobile) {
                menuCarouselDots.style.display = 'none';
                return;
            }

            if (visibleCards.length <= minItemsForDots) {
                menuCarouselDots.style.display = 'none';
                return;
            } else {
                menuCarouselDots.style.display = 'flex';
            }

            const dotCount = Math.min(5, visibleCards.length);

            for (let i = 0; i < dotCount; i++) {
                const dot = document.createElement('div');
                dot.className = `carousel-dot ${i === 0 ? 'active' : ''}`;
                dot.addEventListener('click', () => {
                    let targetCardIndex = i;
                    if (visibleCards.length > 5) {
                        // Map dot index 0..4 back to card index proportionally
                        targetCardIndex = Math.round((i / (dotCount - 1)) * (visibleCards.length - 1));
                    }
                    const card = visibleCards[targetCardIndex];
                    if (card) {
                        const cardWidth = card.offsetWidth + gap; // Dynamic card width + gap
                        menuGrid.scrollTo({
                            left: targetCardIndex * cardWidth,
                            behavior: 'smooth'
                        });
                    }
                });
                menuCarouselDots.appendChild(dot);
            }
        };

        const updateActiveCarouselDot = () => {
            if (!menuCarouselDots) return;
            const visibleCards = Array.from(menuItems).filter(item => item.style.display !== 'none');
            if (visibleCards.length === 0) return;
            
            const isMobile = window.innerWidth <= 768;
            const gap = isMobile ? 20 : 30;
            
            const cardWidth = visibleCards[0].offsetWidth + gap;
            const scrollIndex = Math.round(menuGrid.scrollLeft / cardWidth);
            
            const dots = menuCarouselDots.querySelectorAll('.carousel-dot');
            if (dots.length === 0) return;

            let activeDotIndex = scrollIndex;
            if (visibleCards.length > 5) {
                // Map current scroll index to dot index 0..4 proportionally
                activeDotIndex = Math.min(4, Math.round((scrollIndex / (visibleCards.length - 1)) * (dots.length - 1)));
            }
            
            dots.forEach((dot, idx) => {
                if (idx === activeDotIndex) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        };

        menuGrid.addEventListener('scroll', updateActiveCarouselDot);
        
        window.addEventListener('resize', () => {
            generateCarouselDots();
            updateActiveCarouselDot();
        });

        const filterCategory = (category) => {
            activeCategory = category;
            menuGrid.style.opacity = '0';
            menuGrid.style.transform = 'translateY(10px)';

            setTimeout(() => {
                applyMenuFilters();

                // Scroll menu grid back to start when filtering
                menuGrid.scrollLeft = 0;

                menuGrid.style.opacity = '1';
                menuGrid.style.transform = 'translateY(0)';
            }, 300);
        };

        // Desktop tabs listener
        if (tabBtns.length > 0) {
            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    tabBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    const category = btn.getAttribute('data-category');
                    filterCategory(category);
                    
                    // Sync custom mobile select text & selection highlight
                    if (customSelectTrigger && customOptionsContainer) {
                        const triggerSpan = customSelectTrigger.querySelector('span');
                        const correspondingOption = customOptionsContainer.querySelector(`.custom-option[data-value="${category}"]`);
                        if (correspondingOption) {
                            triggerSpan.textContent = correspondingOption.textContent;
                            customOptionsContainer.querySelectorAll('.custom-option').forEach(opt => opt.classList.remove('selected'));
                            correspondingOption.classList.add('selected');
                        }
                    }
                });
            });
        }

        // Custom Mobile dropdown select toggle listener
        if (customSelectTrigger && customSelectWrapper) {
            customSelectTrigger.addEventListener('click', (e) => {
                e.stopPropagation();
                customSelectWrapper.classList.toggle('open');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                customSelectWrapper.classList.remove('open');
            });
        }

        // Custom options selections listeners
        if (customOptionsContainer) {
            const options = customOptionsContainer.querySelectorAll('.custom-option');
            options.forEach(opt => {
                opt.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const category = opt.getAttribute('data-value');
                    
                    // Highlight selected option
                    options.forEach(o => o.classList.remove('selected'));
                    opt.classList.add('selected');

                    // Update trigger text representation
                    if (customSelectTrigger) {
                        customSelectTrigger.querySelector('span').textContent = opt.textContent;
                    }
                    
                    // Close selector menu
                    if (customSelectWrapper) {
                        customSelectWrapper.classList.remove('open');
                    }

                    // Execute category filter
                    filterCategory(category);

                    // Sync desktop tabs active state if visible
                    if (tabBtns.length > 0) {
                        tabBtns.forEach(btn => {
                            if (btn.getAttribute('data-category') === category) {
                                btn.classList.add('active');
                            } else {
                                btn.classList.remove('active');
                            }
                        });
                    }
                });
            });
        }
        
        menuGrid.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

        // Initial carousel dots load
        generateCarouselDots();
    }

    // ==========================================
    // STICKY CATEGORY NAVBAR DRAG & MOUSE WHEEL SCROLL
    // ==========================================
    const categoryNavTrack = document.getElementById('categoryNavTrack');
    if (categoryNavTrack) {
        let isDown = false;
        let startX;
        let scrollLeft;

        // Mouse Drag to Scroll
        categoryNavTrack.addEventListener('mousedown', (e) => {
            isDown = true;
            categoryNavTrack.classList.add('active-drag');
            startX = e.pageX - categoryNavTrack.offsetLeft;
            scrollLeft = categoryNavTrack.scrollLeft;
        });

        categoryNavTrack.addEventListener('mouseleave', () => {
            isDown = false;
            categoryNavTrack.classList.remove('active-drag');
        });

        categoryNavTrack.addEventListener('mouseup', () => {
            isDown = false;
            categoryNavTrack.classList.remove('active-drag');
        });

        categoryNavTrack.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - categoryNavTrack.offsetLeft;
            const walk = (x - startX) * 1.8;
            categoryNavTrack.scrollLeft = scrollLeft - walk;
        });

        // Mouse Wheel Horizontal Scroll
        categoryNavTrack.addEventListener('wheel', (e) => {
            if (e.deltaY !== 0) {
                e.preventDefault();
                categoryNavTrack.scrollLeft += e.deltaY;
            }
        }, { passive: false });
    }

    // ==========================================
    // CONTINUOUS MENU SCROLL-SPY & NAVIGATOR
    // ==========================================
    const spyLinks = document.querySelectorAll('.nav-scroll-spy-link');
    const menuSections = document.querySelectorAll('.category-menu-section');

    // 1. Smooth Scroll On Category Tab Click
    spyLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('data-target-section');
            const targetEl = document.getElementById(targetId);

            if (targetEl) {
                const categoryBar = document.querySelector('.category-nav-bar-wrapper');
                const headerH = header ? header.offsetHeight : 96;
                const catBarH = categoryBar ? categoryBar.offsetHeight : 45;
                const headerOffset = headerH + catBarH + 10;
                const elementPosition = targetEl.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 2. IntersectionObserver Scroll-Spy
    if (menuSections.length > 0 && 'IntersectionObserver' in window) {
        const observerOptions = {
            root: null,
            rootMargin: '-100px 0px -55% 0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const activeId = entry.target.getAttribute('id');
                    
                    spyLinks.forEach(link => {
                        const target = link.getAttribute('data-target-section');
                        if (target === activeId) {
                            link.classList.add('active', 'selected');
                            if (categoryNavTrack) {
                                const linkLeft = link.offsetLeft;
                                const linkWidth = link.offsetWidth;
                                const trackWidth = categoryNavTrack.offsetWidth;
                                categoryNavTrack.scrollTo({
                                    left: linkLeft - (trackWidth / 2) + (linkWidth / 2),
                                    behavior: 'smooth'
                                });
                            }
                        } else {
                            link.classList.remove('active', 'selected');
                        }
                    });
                }
            });
        }, observerOptions);

        menuSections.forEach(section => observer.observe(section));
    }

    // 3. Floating Back to Top Button
    const backToTopBtn = document.getElementById('backToTopBtn');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 400) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }, { passive: true });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // 4. Universal Continuous Menu Search Handler
    const searchInput = document.getElementById('menuSearchInput');
    if (searchInput && menuSections.length > 0) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();

            menuSections.forEach(section => {
                const cards = section.querySelectorAll('.menu-item-card');
                let matchCount = 0;

                cards.forEach(card => {
                    const title = card.querySelector('h4') ? card.querySelector('h4').textContent.toLowerCase() : '';
                    const desc = card.querySelector('.menu-item-desc') ? card.querySelector('.menu-item-desc').textContent.toLowerCase() : '';
                    
                    if (title.includes(query) || desc.includes(query)) {
                        card.style.display = '';
                        matchCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });

                if (matchCount === 0 && query !== '') {
                    section.style.display = 'none';
                } else {
                    section.style.display = '';
                }
            });
        });
    }

    // ==========================================
    // 7. HOME DEALS SWIPE INDICATOR (MOBILE)
    // ==========================================
    const specialtiesGrid = document.querySelector('.specialties-grid');
    const dealCarouselDots = document.getElementById('dealCarouselDots');

    if (specialtiesGrid && dealCarouselDots) {
        const dealCards = Array.from(specialtiesGrid.querySelectorAll('.menu-item-card, .specialty-card'));
        const dotCount = Math.min(5, dealCards.length);

        for (let i = 0; i < dotCount; i++) {
            const dot = document.createElement('button');
            dot.type = 'button';
            dot.className = `carousel-dot ${i === 0 ? 'active' : ''}`;
            dot.setAttribute('aria-label', `Show deal ${i + 1}`);
            dot.addEventListener('click', () => {
                const cardIndex = dealCards.length > 5
                    ? Math.round((i / (dotCount - 1)) * (dealCards.length - 1))
                    : i;
                specialtiesGrid.scrollTo({ left: dealCards[cardIndex].offsetLeft, behavior: 'smooth' });
            });
            dealCarouselDots.appendChild(dot);
        }

        specialtiesGrid.addEventListener('scroll', () => {
            const cardWidth = dealCards[0].offsetWidth + 20;
            const cardIndex = Math.round(specialtiesGrid.scrollLeft / cardWidth);
            const activeDot = dealCards.length > 5
                ? Math.min(dotCount - 1, Math.round((cardIndex / (dealCards.length - 1)) * (dotCount - 1)))
                : Math.min(dotCount - 1, cardIndex);

            dealCarouselDots.querySelectorAll('.carousel-dot').forEach((dot, index) => {
                dot.classList.toggle('active', index === activeDot);
            });
        });
    }

    // ==========================================
    // 8. PERSISTENT SHOPPING CART SYSTEM (LOCALSTORAGE)
    // ==========================================
    let cart = [];
    const cartToggleBtn = document.getElementById('cartToggleBtn');
    const closeCartBtn = document.getElementById('closeCartBtn');
    const cartSidebar = document.getElementById('cartSidebar');
    const cartOverlay = document.getElementById('cartOverlay');
    const cartItemsContainer = document.getElementById('cartItemsContainer');
    const emptyCartMessage = document.getElementById('emptyCartMessage');
    const cartBadge = document.getElementById('cartBadge');
    const cartSubtotal = document.getElementById('cartSubtotal');
    const cartTotal = document.getElementById('cartTotal');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const mobileCartFab = document.getElementById('mobileCartFab');
    const mobileCartFabBadge = document.getElementById('mobileCartFabBadge');

    // Load Cart from LocalStorage
    const loadCartFromStorage = () => {
        const storedCart = localStorage.getItem('delicious_food_stop_cart');
        if (storedCart) {
            try {
                cart = JSON.parse(storedCart);
            } catch (e) {
                cart = [];
            }
        }
        updateCartUI();
    };

    // Save Cart to LocalStorage
    const saveCartToStorage = () => {
        localStorage.setItem('delicious_food_stop_cart', JSON.stringify(cart));
    };

    // Sidebar Toggling
    const toggleCart = () => {
        if (cartSidebar) cartSidebar.classList.toggle('active');
        if (cartOverlay) cartOverlay.classList.toggle('active');
    };

    if (cartToggleBtn) cartToggleBtn.addEventListener('click', toggleCart);
    if (closeCartBtn) closeCartBtn.addEventListener('click', toggleCart);
    if (cartOverlay) cartOverlay.addEventListener('click', toggleCart);
    if (mobileCartFab) mobileCartFab.addEventListener('click', toggleCart);

    // Add To Order Action (Global Delegation for Deal Cards and Menu Cards)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.add-to-cart-btn');
        if (!btn || btn.disabled || btn.classList.contains('disabled')) return;
        // The product popup has its own handler that adds the selected quantity.
        // Do not let this card-level handler create a second, data-less cart item.
        if (btn.closest('#productDetailModal')) return;

        const card = btn.closest('.menu-item-card, .specialty-card');
        if (card && card.getAttribute('data-in-stock') === 'false') {
            alert('This item is currently out of stock.');
            return;
        }

        // ── Variation intercept ───────────────────────────────────────────────
        // If this card has variations, clicking Add to Cart opens the modal
        // instead of directly adding to cart. Variation selection is required.
        const hasVariations = card && card.getAttribute('data-has-variations') === 'true';
        if (hasVariations) {
            // Gather card data and open the product detail modal
            const imgEl  = card.querySelector('.menu-item-img');
            const h4     = card.querySelector('h4');
            const descEl = card.querySelector('.menu-item-desc');
            const tagEl  = card.querySelector('.menu-item-tag');
            const cardId   = card.getAttribute('data-id') || '';
            const cardName = btn.getAttribute('data-name') || (h4 ? h4.textContent.trim() : '');
            // Base price stored on button; but modal will update to variation price once selected
            const cardPrice = parseFloat(btn.getAttribute('data-price')) || 0;
            const cardImg   = btn.getAttribute('data-img') || (imgEl ? imgEl.src : '');
            const cardDesc  = descEl ? descEl.textContent.trim() : '';
            const cardTag   = tagEl  ? tagEl.textContent.trim()  : '';
            const inStock   = card.getAttribute('data-in-stock') !== 'false';
            // Parse variations from data attribute
            let variations = [];
            try { variations = JSON.parse(card.getAttribute('data-variations') || '[]'); } catch(_) {}
            openProductModal({ id: cardId, name: cardName, price: cardPrice, img: cardImg,
                description: cardDesc, tag: cardTag, inStock, variations });
            return;
        }
        // ─────────────────────────────────────────────────────────────────────

        const itemId   = btn.getAttribute('data-id') || (card ? card.getAttribute('data-id') : 'item-' + Date.now());
        const itemName = btn.getAttribute('data-name') || (card && card.querySelector('h4') ? card.querySelector('h4').textContent : 'Item');

        let itemPrice = parseFloat(btn.getAttribute('data-price'));
        if (isNaN(itemPrice) && card) {
            const priceText = card.querySelector('.menu-item-price') ? card.querySelector('.menu-item-price').textContent : '';
            itemPrice = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0;
        }

        const itemImg = btn.getAttribute('data-img') || (card && card.querySelector('img') ? card.querySelector('img').src : 'images/logo.png');

        // No variation — use productId = itemId, no variation fields
        addItemToCart(itemId, itemId, itemName, itemPrice, itemImg, '', '');

        // Micro-animation feedback on button
        const originalContent = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Added!';
        btn.style.borderColor = '#4caf50';

        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.style.borderColor = '';
        }, 1200);
    });

    let toastTimeout;
    const showCartToast = () => {
        const toast = document.getElementById('cartToast');
        if (!toast) return;

        toast.classList.add('show');
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 3200);
    };

    const cartToastViewBtn = document.getElementById('cartToastViewBtn');
    if (cartToastViewBtn) {
        cartToastViewBtn.addEventListener('click', () => {
            const toast = document.getElementById('cartToast');
            if (toast) toast.classList.remove('show');
            toggleCart();
        });
    }

    /**
     * addItemToCart
     * @param {string} cartKey    Unique cart dedup key. For plain products: item_code.
     *                            For variations: item_code + '-v' + variationId.
     * @param {string} productId  The actual product item_code (sent to the backend).
     * @param {string} name       Product display name.
     * @param {number} price      Selected price (variation price or base price).
     * @param {string} img        Product image URL.
     * @param {string|number} variationId   ProductVariation.id, or '' for plain products.
     * @param {string} variationName  Variation label ('Small', 'Medium'), or '' for plain products.
     */
    const addItemToCart = (cartKey, productId, name, price, img, variationId, variationName) => {
        const existingItem = cart.find(item => item.id === cartKey);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                id: cartKey,
                productId: productId || cartKey,
                name,
                price,
                img,
                quantity: 1,
                variationId: variationId || '',
                variationName: variationName || ''
            });
        }

        saveCartToStorage();
        updateCartUI();
        showCartToast();
    };

    const removeItemFromCart = (id) => {
        cart = cart.filter(item => item.id !== id);
        saveCartToStorage();
        updateCartUI();
    };

    const changeQty = (id, delta) => {
        const item = cart.find(i => i.id === id);
        if (item) {
            item.quantity += delta;
            if (item.quantity <= 0) {
                removeItemFromCart(id);
            } else {
                saveCartToStorage();
                updateCartUI();
            }
        }
    };

    const isRestaurantOpen = document.body.getAttribute('data-is-open') !== 'false';

    const updateCartUI = () => {
        if (!cartItemsContainer) return;

        // Clear dynamic entries
        const dynamicItems = cartItemsContainer.querySelectorAll('.cart-item');
        dynamicItems.forEach(item => item.remove());

        if (cart.length === 0) {
            if (emptyCartMessage) emptyCartMessage.style.display = 'block';
            if (checkoutBtn) checkoutBtn.disabled = true;
            if (cartBadge) cartBadge.textContent = '0';
            if (cartSubtotal) cartSubtotal.textContent = 'Rs. 0';
            if (cartTotal) cartTotal.textContent = 'Rs. 0';
            if (mobileCartFab) mobileCartFab.classList.remove('visible');
        } else {
            if (emptyCartMessage) emptyCartMessage.style.display = 'none';
            if (checkoutBtn) {
                if (!isRestaurantOpen) {
                    checkoutBtn.disabled = true;
                    checkoutBtn.style.opacity = '0.65';
                    checkoutBtn.style.cursor = 'not-allowed';
                    checkoutBtn.style.pointerEvents = 'none';
                } else {
                    checkoutBtn.disabled = false;
                    checkoutBtn.style.opacity = '1';
                    checkoutBtn.style.cursor = 'pointer';
                    checkoutBtn.style.pointerEvents = 'auto';
                }
            }

            let totalQty = 0;
            let subtotal = 0;

            cart.forEach(item => {
                totalQty += item.quantity;
                subtotal += item.price * item.quantity;

                const varBadge = item.variationName
                    ? ` <span class="cart-item-variation">(${item.variationName})</span>`
                    : '';

                const itemEl = document.createElement('div');
                itemEl.className = 'cart-item';
                itemEl.innerHTML = `
                    <img src="${item.img}" alt="${item.name}" class="cart-item-img">
                    <div class="cart-item-details">
                        <div class="cart-item-title-row">
                            <h4>${item.name}${varBadge}</h4>
                            <span class="cart-item-price">Rs. ${(item.price * item.quantity).toFixed(0)}</span>
                        </div>
                        <div class="cart-item-controls">
                            <div class="qty-controls">
                                <button class="qty-btn qty-minus" data-id="${item.id}"><i class="fa-solid fa-minus"></i></button>
                                <span class="qty-num">${item.quantity}</span>
                                <button class="qty-btn qty-plus" data-id="${item.id}"><i class="fa-solid fa-plus"></i></button>
                            </div>
                            <button class="remove-item-btn" data-id="${item.id}">Remove</button>
                        </div>
                    </div>
                `;
                cartItemsContainer.appendChild(itemEl);
            });

            if (cartBadge) cartBadge.textContent = totalQty;
            if (mobileCartFab) mobileCartFab.classList.add('visible');
            if (mobileCartFabBadge) mobileCartFabBadge.textContent = totalQty;

            if (cartSubtotal) cartSubtotal.textContent = `Rs. ${subtotal.toFixed(0)}`;
            if (cartTotal) cartTotal.textContent = `Rs. ${subtotal.toFixed(0)}`;
        }

        attachCartItemListeners();
    };

    const attachCartItemListeners = () => {
        if (!cartItemsContainer) return;
        
        const plusBtns = cartItemsContainer.querySelectorAll('.qty-plus');
        const minusBtns = cartItemsContainer.querySelectorAll('.qty-minus');
        const removeBtns = cartItemsContainer.querySelectorAll('.remove-item-btn');

        plusBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                changeQty(btn.getAttribute('data-id'), 1);
            });
        });

        minusBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                changeQty(btn.getAttribute('data-id'), -1);
            });
        });

        removeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                removeItemFromCart(btn.getAttribute('data-id'));
            });
        });
    };

    // Pre-order success modal checkout logic
    const orderConfirmModal = document.getElementById('orderConfirmModal');
    const closeOrderModalBtn = document.getElementById('closeOrderModalBtn');
    const closeOrderSuccessBtn = document.getElementById('closeOrderSuccessBtn');
    const modalOrderItems = document.getElementById('modalOrderItems');
    const modalOrderTotal = document.getElementById('modalOrderTotal');

    // Customer Checkout Modal Elements
    const customerDetailsModal = document.getElementById('customerDetailsModal');
    const customerDetailsBackdrop = document.getElementById('customerDetailsBackdrop');
    const closeCustomerModalBtn = document.getElementById('closeCustomerModalBtn');
    const customerCheckoutForm = document.getElementById('customerCheckoutForm');
    const custNameInput = document.getElementById('custNameInput');
    const custPhoneInput = document.getElementById('custPhoneInput');
    const custAddressInput = document.getElementById('custAddressInput');

    const closeCustomerModal = () => {
        if (customerDetailsModal) customerDetailsModal.classList.remove('active');
    };

    if (closeCustomerModalBtn) closeCustomerModalBtn.addEventListener('click', closeCustomerModal);
    if (customerDetailsBackdrop) customerDetailsBackdrop.addEventListener('click', closeCustomerModal);

    // Real WhatsApp order handoff
    const WHATSAPP_NUMBER = '923232870355'; // +92 323 2870355, no leading + or 0

    const buildWhatsAppMessage = (name, phone, address) => {
        let msg = `*AMAZING FOODS - NEW ORDER*\n`;
        msg += `------------------------------\n`;
        msg += `*Customer Name:* ${name}\n`;
        msg += `*Phone:* ${phone}\n`;
        msg += `*Address:* ${address}\n`;
        msg += `------------------------------\n`;
        msg += `*Order Items:*\n`;
        cart.forEach((item, index) => {
            // Include variation name in brackets when present
            const varPart = item.variationName ? ` (${item.variationName})` : '';
            msg += `${index + 1}. ${item.name}${varPart} x${item.quantity} - Rs. ${(item.price * item.quantity).toFixed(0)}\n`;
        });
        msg += `------------------------------\n`;
        msg += `*Total Amount:* ${cartTotal ? cartTotal.textContent : ''}\n`;
        return msg;
    };

    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', (e) => {
            if (!isRestaurantOpen) {
                e.preventDefault();
                alert('Ordering is currently unavailable because the restaurant is closed. Please visit again during our opening hours.');
                return false;
            }
            if (cart.length === 0) return;

            // 1. Close cart sidebar drawer
            if (cartSidebar && cartSidebar.classList.contains('active')) {
                toggleCart();
            }

            // 2. Open Customer Details Modal
            if (customerDetailsModal) {
                customerDetailsModal.classList.add('active');
                if (custNameInput) custNameInput.focus();
            }
        });
    }

    if (customerCheckoutForm) {
        customerCheckoutForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const name = custNameInput ? custNameInput.value.trim() : '';
            const phone = custPhoneInput ? custPhoneInput.value.trim() : '';
            const address = custAddressInput ? custAddressInput.value.trim() : '';

            if (!name || !phone || !address) {
                alert('Please fill in your Name, Phone Number, and Delivery Address to proceed.');
                return false;
            }

            if (cart.length === 0) {
                alert('Your cart is empty.');
                closeCustomerModal();
                return false;
            }

            // 1. Open WhatsApp with formatted message including customer details
            const waUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(buildWhatsAppMessage(name, phone, address))}`;
            window.open(waUrl, '_blank') || (window.location.href = waUrl);

            // 2. Save order to backend database with customer details
            // Map cart items to the shape api_create_order expects:
            // { id: productId, name, price, quantity, variation_name }
            const cartPayload = cart.map(item => ({
                id: item.productId || item.id,   // always the product item_code
                name: item.name,
                price: item.price,
                quantity: item.quantity,
                variation_name: item.variationName || ''
            }));
            fetch('/create-order/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer_name: name,
                    customer_phone: phone,
                    delivery_address: address,
                    order_notes: '',
                    cart_items: cartPayload
                })
            }).catch(err => console.log('Background order sync error:', err));

            // 3. Populate confirmation modal order items
            if (modalOrderItems) {
                modalOrderItems.innerHTML = '';
                cart.forEach(item => {
                    const varLabel = item.variationName ? ` (${item.variationName})` : '';
                    const row = document.createElement('div');
                    row.className = 'order-details-item';
                    row.innerHTML = `
                        <span>${item.name}${varLabel} <span class="qty">x${item.quantity}</span></span>
                        <span>Rs. ${(item.price * item.quantity).toFixed(0)}</span>
                    `;
                    modalOrderItems.appendChild(row);
                });
            }

            if (modalOrderTotal) {
                modalOrderTotal.textContent = cartTotal ? cartTotal.textContent : '';
            }

            // 4. Close Customer Modal & Show Success Confirmation Modal
            closeCustomerModal();
            if (orderConfirmModal) orderConfirmModal.classList.add('active');

            // 5. Clear cart
            cart = [];
            saveCartToStorage();
            updateCartUI();
        });
    }

    const closeOrderModal = () => {
        if (orderConfirmModal) orderConfirmModal.classList.remove('active');
    };

    if (closeOrderModalBtn) closeOrderModalBtn.addEventListener('click', closeOrderModal);
    if (closeOrderSuccessBtn) closeOrderSuccessBtn.addEventListener('click', closeOrderModal);
    
    const orderConfirmBackdrop = document.getElementById('orderConfirmBackdrop');
    if (orderConfirmBackdrop) orderConfirmBackdrop.addEventListener('click', closeOrderModal);

    // Initialize cart state
    loadCartFromStorage();

    // ==========================================
    // 9. PRODUCT DETAIL POPUP MODAL
    // ==========================================
    const productDetailModal = document.getElementById('productDetailModal');
    const closeProductModalBtn = document.getElementById('closeProductModalBtn');
    const modalProductImg   = document.getElementById('modalProductImg');
    const modalProductName  = document.getElementById('modalProductName');
    const modalProductDesc  = document.getElementById('modalProductDesc');
    const modalProductPrice = document.getElementById('modalProductPrice');
    const modalProductTag   = document.getElementById('modalProductTag');
    const modalQtyVal       = document.getElementById('modalQtyVal');
    const modalQtyMinus     = document.getElementById('modalQtyMinus');
    const modalQtyPlus      = document.getElementById('modalQtyPlus');
    const modalAddToCartBtn = document.getElementById('modalAddToCartBtn');
    let modalAddToCartTotal = document.getElementById('modalAddToCartTotal');

    // State for the currently-open modal item
    let _modalData = {
        id: '', cartKey: '', productId: '', name: '', price: 0, img: '', qty: 1,
        variationId: '', variationName: '', variations: []
    };

    const updateModalQuantityUI = () => {
        if (modalQtyVal) modalQtyVal.textContent = _modalData.qty;
        if (modalAddToCartTotal) {
            modalAddToCartTotal.textContent = `Rs. ${Math.round(_modalData.price * _modalData.qty).toLocaleString('en-US')}`;
        }
    };

    /**
     * Render variation selector buttons inside #modalVariationSelector.
     * Clicking a button selects that variation and updates the displayed price.
     * If variations is empty, the selector is hidden.
     */
    const renderVariationSelector = (variations) => {
        const selector = document.getElementById('modalVariationSelector');
        if (!selector) return;

        if (!variations || variations.length === 0) {
            selector.style.display = 'none';
            selector.innerHTML = '';
            return;
        }

        selector.style.display = '';
        selector.innerHTML = `
            <span class="modal-variation-label">Choose Size / Variation</span>
            <div class="modal-variation-options" id="modalVariationOptions"></div>
            <span class="modal-variation-hint" id="modalVariationHint">Please select a size to continue.</span>
        `;

        const optionsRow = document.getElementById('modalVariationOptions');
        variations.forEach(v => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'modal-variation-btn';
            btn.setAttribute('data-var-id', v.id);
            btn.setAttribute('data-var-name', v.name);
            btn.setAttribute('data-var-price', v.price);
            btn.innerHTML = `<span class="var-name">${v.name}</span><span class="var-price">Rs. ${Math.round(v.price).toLocaleString('en-US')}</span>`;

            btn.addEventListener('click', () => {
                // Deselect all, select this one
                optionsRow.querySelectorAll('.modal-variation-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');

                // Update modal state
                _modalData.variationId   = v.id;
                _modalData.variationName = v.name;
                _modalData.price         = parseFloat(v.price);
                _modalData.cartKey       = `${_modalData.id}-v${v.id}`;

                // Update price display and total button
                if (modalProductPrice)
                    modalProductPrice.textContent = `Rs. ${Math.round(v.price).toLocaleString('en-US')}`;
                updateModalQuantityUI();

                // Hide the "please select" hint
                const hint = document.getElementById('modalVariationHint');
                if (hint) hint.classList.remove('visible');

                // Re-enable the add button if it was blocked
                if (modalAddToCartBtn && modalAddToCartBtn.disabled !== true) {
                    modalAddToCartBtn.disabled = false;
                    modalAddToCartBtn.style.opacity = '';
                }
            });

            optionsRow.appendChild(btn);
        });
    };

    const openProductModal = (data) => {
        if (!productDetailModal) return;

        // Initialise modal state
        const variations = data.variations || [];
        _modalData = {
            id:            data.id || '',
            cartKey:       data.id || '',   // overwritten when variation selected
            productId:     data.id || '',
            name:          data.name || '',
            price:         parseFloat(data.price) || 0,
            img:           data.img || '',
            qty:           1,
            variationId:   '',
            variationName: '',
            variations:    variations
        };

        // Populate static fields
        modalProductImg.src             = data.img;
        modalProductImg.alt             = data.name;
        modalProductName.textContent    = data.name;
        modalProductDesc.textContent    = data.description || '';
        modalProductDesc.style.display  = data.description ? '' : 'none';
        modalProductPrice.textContent   = `Rs. ${Math.round(data.price).toLocaleString('en-US')}`;

        if (modalProductTag) {
            if (data.tag) {
                modalProductTag.textContent    = data.tag;
                modalProductTag.style.display  = '';
            } else {
                modalProductTag.style.display  = 'none';
            }
        }

        // Render variation selector (hides itself if no variations)
        renderVariationSelector(variations);

        // Configure Add to Cart button
        if (modalAddToCartBtn) {
            if (data.inStock === false) {
                modalAddToCartBtn.disabled = true;
                modalAddToCartBtn.innerHTML = '<span>Out of Stock</span>';
                modalAddToCartBtn.style.opacity = '0.6';
                modalAddToCartBtn.style.cursor  = 'not-allowed';
            } else {
                modalAddToCartBtn.disabled = false;
                modalAddToCartBtn.innerHTML = '<span id="modalAddToCartTotal" class="product-modal-add-total">Rs. 0</span><span class="product-modal-add-label">Add To Cart</span>';
                modalAddToCartTotal = document.getElementById('modalAddToCartTotal');
                modalAddToCartBtn.style.opacity = '';
                modalAddToCartBtn.style.cursor  = '';
            }
        }

        updateModalQuantityUI();
        const modalBodyScroll = productDetailModal.querySelector('.product-modal-body-scroll');
        if (modalBodyScroll) modalBodyScroll.scrollTop = 0;

        productDetailModal.classList.add('active');
        productDetailModal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('product-modal-open');
        document.body.style.overflow = 'hidden';
    };

    const closeProductModal = () => {
        if (!productDetailModal) return;
        productDetailModal.classList.remove('active');
        productDetailModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('product-modal-open');
        document.body.style.overflow = '';
        _modalData = { id: '', cartKey: '', productId: '', name: '', price: 0, img: '', qty: 1, variationId: '', variationName: '', variations: [] };
    };

    // Close via × button
    if (closeProductModalBtn) {
        closeProductModalBtn.addEventListener('click', closeProductModal);
    }

    // Close via backdrop click (clicking the dark area outside the container)
    if (productDetailModal) {
        productDetailModal.addEventListener('click', (e) => {
            if (e.target === productDetailModal) closeProductModal();
        });
    }

    // Close via Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && productDetailModal && productDetailModal.classList.contains('active')) {
            closeProductModal();
        }
    });

    // ── Card click → open modal (but NOT when clicking Add to Cart) ──
    // Uses event delegation on document so it also covers dynamically injected cards (menu.html AJAX)
    document.addEventListener('click', (e) => {
        // Ignore if click came from an add-to-cart button (or any element inside it)
        if (e.target.closest('.add-to-cart-btn')) return;
        // Ignore if click came from a modal element itself
        if (e.target.closest('#productDetailModal')) return;

        const card = e.target.closest('.menu-item-card');
        if (!card) return;

        // Gather data from the card's DOM
        const btn = card.querySelector('.add-to-cart-btn');
        const imgEl  = card.querySelector('.menu-item-img');
        const h4     = card.querySelector('h4');
        const descEl = card.querySelector('.menu-item-desc');
        const tagEl  = card.querySelector('.menu-item-tag');

        const id    = btn ? btn.getAttribute('data-id')    : card.getAttribute('data-id') || '';
        const name  = btn ? btn.getAttribute('data-name')  : (h4 ? h4.textContent.trim() : '');
        const price = btn ? parseFloat(btn.getAttribute('data-price')) : 0;
        const img   = btn ? btn.getAttribute('data-img')   : (imgEl ? imgEl.src : '');
        const desc  = descEl ? descEl.textContent.trim() : '';
        const tag   = tagEl  ? tagEl.textContent.trim()  : '';
        const inStock = card.getAttribute('data-in-stock') !== 'false';

        // Parse variations from data attribute (present only for products with variations)
        let variations = [];
        try { variations = JSON.parse(card.getAttribute('data-variations') || '[]'); } catch(_) {}

        openProductModal({ id, name, price, img, description: desc, tag, inStock, variations });
    });

    // Quantity controls inside modal
    if (modalQtyMinus) {
        modalQtyMinus.addEventListener('click', () => {
            if (_modalData.qty > 1) {
                _modalData.qty -= 1;
                updateModalQuantityUI();
            }
        });
    }

    if (modalQtyPlus) {
        modalQtyPlus.addEventListener('click', () => {
            _modalData.qty += 1;
            updateModalQuantityUI();
        });
    }

    // "Add to Order" button inside the modal
    if (modalAddToCartBtn) {
        modalAddToCartBtn.addEventListener('click', () => {
            if (!_modalData.id || modalAddToCartBtn.disabled) return;

            // If this product has variations, the customer must pick one first
            if (_modalData.variations.length > 0 && !_modalData.variationId) {
                const hint = document.getElementById('modalVariationHint');
                if (hint) hint.classList.add('visible');
                return;
            }

            // Add once with the correct quantity
            addItemToCart(
                _modalData.cartKey,
                _modalData.productId,
                _modalData.name,
                _modalData.price,
                _modalData.img,
                _modalData.variationId,
                _modalData.variationName
            );
            // Then increment by remaining qty - 1
            for (let i = 1; i < _modalData.qty; i++) {
                addItemToCart(
                    _modalData.cartKey,
                    _modalData.productId,
                    _modalData.name,
                    _modalData.price,
                    _modalData.img,
                    _modalData.variationId,
                    _modalData.variationName
                );
            }

            // Visual feedback on the modal button
            const origHtml = modalAddToCartBtn.innerHTML;
            modalAddToCartBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Added!';
            setTimeout(() => { modalAddToCartBtn.innerHTML = origHtml; }, 1200);

            closeProductModal();
        });
    }


    // Seating layout & bookings wizard script sections removed as reservations page was retired.

    // ==========================================
    // 10. REAL-TIME OPERATIONAL BADGE STATUS
    // ==========================================
    const liveStatusBadge = document.getElementById('liveStatusBadge');
    
    const checkLiveOperatingStatus = () => {
        if (!liveStatusBadge) return;

        const now = new Date();
        const hour = now.getHours();

        if (hour >= 11 && hour < 22) {
            liveStatusBadge.textContent = 'Open Now';
            liveStatusBadge.className = 'status-badge open';
        } else {
            liveStatusBadge.textContent = 'Closed Now — Opens at 11 AM';
            liveStatusBadge.className = 'status-badge closed';
        }
    };

    // Initialize floating labels
    initFloatingLabels();
});

// Floating label logic
function initFloatingLabels() {
    document.querySelectorAll('.floating-group').forEach(group => {
        const input = group.querySelector('.floating-input');
        if (!input) return;
        const updateState = () => {
            if (input.value && input.value.trim() !== '') {
                group.classList.add('has-value', 'is-filled');
            } else {
                group.classList.remove('has-value', 'is-filled');
            }
        };
        input.addEventListener('focus', () => group.classList.add('focused'));
        input.addEventListener('blur', () => { group.classList.remove('focused'); updateState(); });
        input.addEventListener('input', updateState);
        input.addEventListener('change', updateState);
        input.addEventListener('keyup', updateState);
        updateState();
    });
}

/* ==========================================================================
   EXTENSIBLE & HIGH-PERFORMANCE HERO VIDEO CAROUSEL (Video Completion Triggered)
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
    const heroWrapper = document.getElementById('heroCarouselWrapper');
    if (!heroWrapper) return;

    const slides = Array.from(heroWrapper.querySelectorAll('.hero-slide'));
    const dotsContainer = document.getElementById('heroCarouselDots');
    const prevBtn = document.getElementById('heroPrevBtn');
    const nextBtn = document.getElementById('heroNextBtn');

    if (slides.length <= 1) return;

    let currentIndex = 0;
    let fallbackTimer = null;
    const FALLBACK_DURATION = 6500; // 6.5s safety fallback timer

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Secondary carousel videos start without a source so they do not compete
    // with the visible hero video during the page's initial load.
    const loadDeferredVideo = (video) => {
        if (!video || video.dataset.loaded === 'true' || !video.dataset.webmSrc) return;

        const webmSource = document.createElement('source');
        webmSource.src = video.dataset.webmSrc;
        webmSource.type = 'video/webm';

        const mp4Source = document.createElement('source');
        mp4Source.src = video.dataset.mp4Src;
        mp4Source.type = 'video/mp4';

        video.append(webmSource, mp4Source);
        video.dataset.loaded = 'true';
        video.load();
    };

    const handleNext = () => {
        const nextIdx = (currentIndex + 1) % slides.length;
        goToSlide(nextIdx);
    };

    const handlePrev = () => {
        const prevIdx = (currentIndex - 1 + slides.length) % slides.length;
        goToSlide(prevIdx);
    };

    const goToSlide = (nextIndex) => {
        if (nextIndex < 0) nextIndex = slides.length - 1;
        if (nextIndex >= slides.length) nextIndex = 0;

        if (fallbackTimer) clearTimeout(fallbackTimer);

        slides.forEach((slide, idx) => {
            const video = slide.querySelector('video');
            if (idx === nextIndex) {
                slide.style.display = 'block';
                slide.classList.add('active');
                if (video) {
                    loadDeferredVideo(video);
                    video.muted = true;
                    video.playsInline = true;
                    video.currentTime = 0;
                    
                    // When video completes playing, automatically transition to next slide
                    video.onended = () => {
                        if (!prefersReducedMotion) {
                            handleNext();
                        }
                    };

                    const p = video.play();
                    if (p !== undefined) {
                        p.catch(() => {
                            video.muted = true;
                            video.play().catch(() => {});
                        });
                    }
                }
            } else {
                slide.classList.remove('active');
                slide.style.display = 'none';
                if (video) {
                    video.onended = null;
                    try { video.pause(); } catch(e) {}
                }
            }
        });

        // Safety fallback timer if video ended event is delayed
        if (!prefersReducedMotion) {
            fallbackTimer = setTimeout(handleNext, FALLBACK_DURATION);
        }

        // Update indicators
        if (dotsContainer) {
            const dots = dotsContainer.querySelectorAll('.hero-dot');
            dots.forEach((dot, idx) => {
                dot.classList.toggle('active', idx === nextIndex);
            });
        }

        currentIndex = nextIndex;
    };

    if (nextBtn) nextBtn.addEventListener('click', () => { handleNext(); });
    if (prevBtn) prevBtn.addEventListener('click', () => { handlePrev(); });

    if (dotsContainer) {
        dotsContainer.addEventListener('click', (e) => {
            const dot = e.target.closest('.hero-dot');
            if (!dot) return;
            const targetIdx = parseInt(dot.getAttribute('data-slide-to'), 10);
            if (!isNaN(targetIdx)) {
                goToSlide(targetIdx);
            }
        });
    }

    // Touch Swipe Support (Mobile & Tablet)
    let touchStartX = 0;
    let touchStartY = 0;
    const SWIPE_THRESHOLD = 40; // Minimum 40px swipe distance

    heroWrapper.addEventListener('touchstart', (e) => {
        if (e.touches && e.touches.length > 0) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }
    }, { passive: true });

    heroWrapper.addEventListener('touchend', (e) => {
        if (e.changedTouches && e.changedTouches.length > 0) {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;

            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;

            // Ensure swipe is horizontal (deltaX > deltaY) and exceeds threshold
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) >= SWIPE_THRESHOLD) {
                if (deltaX < 0) {
                    handleNext(); // Swipe Left -> Next Slide
                } else {
                    handlePrev(); // Swipe Right -> Prev Slide
                }
            }
        }
    }, { passive: true });

    // Mouse Drag Swipe Support (Desktop)
    let isMouseDown = false;
    let mouseStartX = 0;

    heroWrapper.addEventListener('mousedown', (e) => {
        isMouseDown = true;
        mouseStartX = e.clientX;
    });

    heroWrapper.addEventListener('mouseup', (e) => {
        if (!isMouseDown) return;
        isMouseDown = false;
        const deltaX = e.clientX - mouseStartX;
        if (Math.abs(deltaX) >= SWIPE_THRESHOLD) {
            if (deltaX < 0) {
                handleNext();
            } else {
                handlePrev();
            }
        }
    });

    heroWrapper.addEventListener('mouseleave', () => {
        isMouseDown = false;
    });

    // Initial activation
    goToSlide(0);
});
