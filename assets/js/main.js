/*-----------------------------------------------------------------

Template Name:  Industril - Factory and Industrial HTML Template
Author:  EaglesThemes
Author URI: https://themeforest.net/user/eaglesthemes/portfolio
Developer: MR Tanvir
Version: 1.0.0
Description: Industril - Factory and Industrial HTML Template

-------------------------------------------------------------------
CSS TABLE OF CONTENTS
-------------------------------------------------------------------

01. preloader
02. header
03. swiper slider
04. animated text with swiper slider
05. mouse cursor
06. active js
07. magnificPopup
08. back to top
09. coundown 
10. nice select
11. wow animation

------------------------------------------------------------------*/

(function($) {
    "use strict";

    $(document).ready( function() {

        //>> Mobile Menu Js Start <<//
        $('#mobile-menu').meanmenu({
            meanMenuContainer: '.mobile-menu',
            meanScreenWidth: "991",
            meanExpand: ['<i class="far fa-plus"></i>'],
        });

        //>> Sidebar Toggle Js Start <<//
        $(".offcanvas__close,.offcanvas__overlay").on("click", function() {
            $(".offcanvas__info").removeClass("info-open");
            $(".offcanvas__overlay").removeClass("overlay-open");
        });
        $(".sidebar__toggle").on("click", function() {
            $(".offcanvas__info").addClass("info-open");
            $(".offcanvas__overlay").addClass("overlay-open");
        });

        //>> Body Overlay Js Start <<//
        $(".body-overlay").on("click", function() {
            $(".offcanvas__area").removeClass("offcanvas-opened");
            $(".df-search-area").removeClass("opened");;
            $(".body-overlay").removeClass("opened");
        });

        //>> Sticky Header Js Start <<//

        $(window).scroll(function() {
            if ($(this).scrollTop() > 250) {
                $("#header-sticky").addClass("sticky");
            } else {
                $("#header-sticky").removeClass("sticky");
            }
        });

        //>> Hero Slider Start <<//
        const sliderActive1 = ".hero-slider";
        const sliderInit1 = new Swiper(sliderActive1, {
            loop: true,
            slidesPerView: 1,
            effect: "fade",
            speed: 2000,
            autoplay: {
            delay: 4000,
            disableOnInteraction: false,
            },
            pagination: {
            el: ".dot",
            clickable: true,
        },
            
        });
        // content animation when active start here
        function animated_swiper(selector, init) {
            let animated = function animated() {
                $(selector + " [data-animation]").each(function () {
                    let anim = $(this).data("animation");
                    let delay = $(this).data("delay");
                    let duration = $(this).data("duration");
                    $(this)
                        .removeClass("anim" + anim)
                        .addClass(anim + " animated")
                        .css({
                            webkitAnimationDelay: delay,
                            animationDelay: delay,
                            webkitAnimationDuration: duration,
                            animationDuration: duration,
                        })
                        .one("animationend", function () {
                            $(this).removeClass(anim + " animated");
                        });
                });
            };
            animated();
            init.on("slideChange", function () {
                $(sliderActive1 + " [data-animation]").removeClass("animated");
            });
            init.on("slideChange", animated);
        }
         animated_swiper(sliderActive1, sliderInit1);

        //>> Hero-1 Slider Start <<//
        const sliderActive2 = ".hero-slider-2";
        const sliderInit2 = new Swiper(sliderActive2, {
            loop: true,
            slidesPerView: 1,
            effect: "fade",
            speed: 3000,
            autoplay: {
                delay: 7000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".arry-prev",
                prevEl: ".arry-next",
            },
            pagination: {
                el: ".dot",
                clickable: true,
            },
        });
        function animated_swiper(selector, init) {
            const animated = function animated() {
                $(selector + " [data-animation]").each(function () {
                    let anim = $(this).data("animation");
                    let delay = $(this).data("delay");
                    let duration = $(this).data("duration");
                    $(this)
                        .removeClass("anim" + anim)
                        .addClass(anim + " animated")
                        .css({
                            webkitAnimationDelay: delay,
                            animationDelay: delay,
                            webkitAnimationDuration: duration,
                            animationDuration: duration,
                        })
                        .one("animationend", function () {
                            $(this).removeClass(anim + " animated");
                        });
                });
            };
            animated();
            init.on("slideChange", function () {
                $(sliderActive2 + " [data-animation]").removeClass("animated");
            });
            init.on("slideChange", animated);
        }
        animated_swiper(sliderActive2, sliderInit2);

  
        //>> Video Popup Start <<//
        $(".img-popup").magnificPopup({
            type: "image",
            gallery: {
                enabled: true,
            },
        });

        $('.video-popup').magnificPopup({
            type: 'iframe',
            callbacks: {
            }
        });
        
        //>> Counterup Start <<//
        $(".count").counterUp({
            delay: 15,
            time: 4000,
        });

        //>> Wow Animation Start <<//
        new WOW().init();

        //>> Nice Select Start <<//
        $('select').niceSelect();

         //>> Active Js Start <<//
         $(".contact-info-items").hover(
            function() {
                $(".contact-info-items").removeClass("active");
                $(this).addClass("active");
            }
        );

         //>> Scroll Js Start <<//
         const scrollPath = document.querySelector(".scroll-up path");
         const pathLength = scrollPath.getTotalLength();
         scrollPath.style.transition = scrollPath.style.WebkitTransition = "none";
         scrollPath.style.strokeDasharray = pathLength + " " + pathLength;
         scrollPath.style.strokeDashoffset = pathLength;
         scrollPath.getBoundingClientRect();
         scrollPath.style.transition = scrollPath.style.WebkitTransition = "stroke-dashoffset 10ms linear";
 
         const updatescroll = function() {
             let scrolltotal = $(window).scrollTop();
             let height = $(document).height() - $(window).height();
             let scrolltotalheight = pathLength - (scrolltotal * pathLength) / height;
             scrollPath.style.strokeDashoffset = scrolltotalheight;
         };
         updatescroll();
 
         $(window).scroll(updatescroll);
         const offset = 50;
         const duration = 950;
 
         $(window).on("scroll", function() {
             if (jQuery(this).scrollTop() > offset) {
                 jQuery(".scroll-up").addClass("active-scroll");
             } else {
                 jQuery(".scroll-up").removeClass("active-scroll");
             }
         });
 
         $(".scroll-up").on("click", function(event) {
             event.preventDefault();
             jQuery("html, body").animate({
                     scrollTop: 0,
                 },
                 duration
             );
             return false;
         });

        //>> Project Slider Start <<//
        const projectSlider = new Swiper(".project-slider", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".dot-3",
                clickable: true,
            },
            breakpoints: {
                1199: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 2,
                },
                767: {
                    slidesPerView: 2,
                },
                575: {
                    slidesPerView: 1,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });

        //>> Project Content Slider Start <<//
        const projectContentSlider = new Swiper(".project-content-slider", {
            speed: 1000,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".pegi-number",
                type: "fraction",
            },
            navigation: {
                nextEl: ".arry-prev",
                prevEl: ".arry-next",
            },
        });

        //>> Project Image Slider Start <<//
        const projectImageSlider = new Swiper(".project-image-slider", {
            speed: 1000,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".pegi-number",
                type: "fraction",
            },
            navigation: {
                nextEl: ".arry-prev",
                prevEl: ".arry-next",
            },
        });

        projectContentSlider.controller.control = projectImageSlider;
        projectImageSlider.controller.control = projectContentSlider;

        //>> Testimonial Image Slider Start <<//
        const testimonialImageSlider = new Swiper(".testimonial-image-slider", {
            speed: 1000,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".dot-2",
                clickable: true,
            },
        });

        //>> Testimonial Content Slider Start <<//
        const testimonialContentSlider = new Swiper(".testimonial-content-slider", {
            speed: 1000,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".dot-2",
                clickable: true,
            },
        });

        testimonialImageSlider.controller.control = testimonialContentSlider;
        testimonialContentSlider.controller.control = testimonialImageSlider;

        //>> Testimonial Content Slider Start <<//
        const testimonialSlider = new Swiper(".testimonial-slider", {
            speed: 1500,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 3000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".arry-prev",
                prevEl: ".arry-next",
            },
        });

        const testimonialSlider2 = new Swiper(".testimonial-slider-2", {
            spaceBetween: 30,
            speed: 1500,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 3000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".dot-2",
                clickable: true,
            },
            breakpoints: {
                1199: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 2,
                },
                767: {
                    slidesPerView: 2,
                },
                575: {
                    slidesPerView: 1,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });

        //>> Service Slider Start <<//
        const serviceSlider = new Swiper(".service-slider", {
            loop: "true",
            spaceBetween: 24,
            speed: 800,
            autoplay: {
                delay: 4000,
                disableOnInteraction: false,
            },
             pagination: {
                el: ".dot",
                clickable: true,
            },
            breakpoints: {
            1440: {
                slidesPerView: 4,
            },
            992: {
                slidesPerView: 3,
            },
            575: {
                slidesPerView: 2,
            },
            320: {
                slidesPerView: 1,
            },
        },
        });

        const serviceSlider2 = new Swiper(".service-slider-2", {
            loop: "true",
            spaceBetween: 24,
            speed: 800,
            autoplay: {
                delay: 4000,
                disableOnInteraction: false,
            },
            pagination: {
                el: ".dot-3",
                clickable: true,
            },
            breakpoints: {
            1199: {
                slidesPerView: 3,
            },
            992: {
                slidesPerView: 2,
            },
            575: {
                slidesPerView: 1,
            },
            320: {
                slidesPerView: 1,
            },
        },
        });

        // Background image date area start here ***
        $("[data-background").each(function () {
            $(this).css(
                "background-image",
                "url( " + $(this).attr("data-background") + "  )"
            );
        });

        // Image src and class add js area start here ***
        $(document).on("mouseenter", ".changeImage2", function () {
            let newImage = $(this).data("image");
            let fadeDuration = 200;

            $("#myImage2").fadeOut(fadeDuration, function () {
                $("#myImage2").attr("src", newImage);
                $("#myImage2").fadeIn(fadeDuration);
            });

            $(this).addClass("clicked");
            $(".changeImage2").not(this).removeClass("clicked");
        });
        // Image src and class add js area end here ***

        //>> Mouse Cursor Start <<//
        function mousecursor() {
            if ($("body")) {
                const e = document.querySelector(".cursor-inner"),
                    t = document.querySelector(".cursor-outer");
                let n,
                    i = 0,
                    o = !1;
                (window.onmousemove = function(s) {
                    o ||
                        (t.style.transform =
                            "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                        (e.style.transform =
                            "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                        (n = s.clientY),
                        (i = s.clientX);
                }),
                $("body").on("mouseenter", "a, .cursor-pointer", function() {
                        e.classList.add("cursor-hover"), t.classList.add("cursor-hover");
                    }),
                    $("body").on("mouseleave", "a, .cursor-pointer", function() {
                        ($(this).is("a") && $(this).closest(".cursor-pointer").length) ||
                        (e.classList.remove("cursor-hover"),
                            t.classList.remove("cursor-hover"));
                    }),
                    (e.style.visibility = "visible"),
                    (t.style.visibility = "visible");
            }
        }
        $(function() {
            mousecursor();
        });


    }); // End Document Ready Function

    function loader() {
        $(window).on('load', function() {
            // Animate loader off screen
            $(".preloader").addClass('loaded');                    
            $(".preloader").delay(600).fadeOut();                       
        });
    }

    loader();

    /*=============================================
		=           Add/Has/Remove        =
	=============================================*/
	$(document).ready(function () {
		$('.team-item-2 , .services-item-2').mouseenter(function () {
			$('.team-item-2 , .services-item-2').removeClass("active");
			$(this).addClass("active");
		});
	});
   

})(jQuery); // End jQuery

