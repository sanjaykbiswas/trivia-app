// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get all screens
    const screens = document.querySelectorAll('.screen');
    const splashScreen = document.getElementById('splash-screen');
    const onboardingScreen = document.getElementById('onboarding-screen');
    const homeScreen = document.getElementById('home-screen');
    const gameSetupScreen = document.getElementById('game-setup-screen');
    const gameOptionsScreen = document.getElementById('game-options-screen');
    const questionScreen = document.getElementById('question-screen');

    // Get modals
    const signInModal = document.getElementById('sign-in-modal');
    const displayNameModal = document.getElementById('display-name-modal');

    // Get buttons
    const getStartedBtn = document.getElementById('get-started-btn');
    const signInBtn = document.getElementById('sign-in-btn');
    const soloOption = document.getElementById('solo-option');
    const partyOption = document.getElementById('party-option');
    const startGameBtn = document.getElementById('start-game-btn');
    const backButtons = document.querySelectorAll('.back-button');
    const closeButtons = document.querySelectorAll('.close-button');

    // Get pack cards
    const packCards = document.querySelectorAll('.pack-card');

    // Animated typing effect variables
    const typingText = document.getElementById('typing-text');
    const phrases = [
        { text: "dinners with friends", color: "#FF5733" },
        { text: "in cities where none of us live", color: "#33A8FF" },
        { text: "competitive spirits", color: "#9C33FF" },
        { text: "rainy days on the couch", color: "#33FFBD" },
        { text: "bathroom breaks", color: "#FF33A8" },
        { text: "long car rides", color: "#33FF57" },
        { text: "game nights", color: "#FFD133" }
    ];
    let currentPhraseIndex = 0;
    let currentCharIndex = 0;
    let isDeleting = false;
    let isWaiting = false;

    // Helper function to show a specific screen
    function showScreen(screen) {
        screens.forEach(s => s.classList.remove('active'));
        screen.classList.add('active');
    }

    // Helper function to show a modal
    function showModal(modal) {
        modal.classList.add('show');
    }

    // Helper function to hide a modal
    function hideModal(modal) {
        modal.classList.remove('show');
    }

    // Start with splash screen, then move to onboarding
    showScreen(splashScreen);
    setTimeout(() => {
        showScreen(onboardingScreen);
        startTypingEffect();
    }, 2000);

    // Typing effect function
    function startTypingEffect() {
        const currentPhrase = phrases[currentPhraseIndex];
        const speed = isDeleting ? 50 : 100;
        
        // Update text and color
        typingText.textContent = currentPhrase.text.substring(0, currentCharIndex);
        typingText.style.color = currentPhrase.color;
        
        // Handle typing logic
        if (!isDeleting && currentCharIndex === currentPhrase.text.length) {
            // Complete word - wait before deleting
            isWaiting = true;
            setTimeout(() => {
                isWaiting = false;
                isDeleting = true;
                typeNextChar();
            }, 1500);
        } else if (isDeleting && currentCharIndex === 0) {
            // Fully deleted - move to next phrase
            isDeleting = false;
            currentPhraseIndex = (currentPhraseIndex + 1) % phrases.length;
            typeNextChar();
        } else {
            // Continue typing or deleting
            if (!isWaiting) {
                currentCharIndex = isDeleting ? currentCharIndex - 1 : currentCharIndex + 1;
                setTimeout(typeNextChar, speed);
            }
        }
    }

    function typeNextChar() {
        startTypingEffect();
    }

    // Setup event listeners for navigation
    getStartedBtn.addEventListener('click', () => {
        showScreen(homeScreen);
    });

    signInBtn.addEventListener('click', () => {
        showModal(signInModal);
    });

    soloOption.addEventListener('click', () => {
        showModal(displayNameModal);
        // Normally would check for temp user here, but we'll simulate the flow
    });

    partyOption.addEventListener('click', () => {
        showModal(displayNameModal);
    });

    // After display name is entered
    document.querySelector('#display-name-modal .primary-button').addEventListener('click', () => {
        hideModal(displayNameModal);
        showScreen(gameSetupScreen);
    });

    // Pack selection
    packCards.forEach(card => {
        card.addEventListener('click', () => {
            const packTitle = card.getAttribute('data-title') || 'Selected Pack';
            document.getElementById('pack-title').textContent = packTitle;
            showScreen(gameOptionsScreen);
        });
    });

    // Start the game
    startGameBtn.addEventListener('click', () => {
        showScreen(questionScreen);
    });

    // Set up back buttons
    backButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Simple history navigation, would be more complex in a real app
            if (gameOptionsScreen.classList.contains('active')) {
                showScreen(gameSetupScreen);
            } else if (gameSetupScreen.classList.contains('active')) {
                showScreen(homeScreen);
            } else if (homeScreen.classList.contains('active')) {
                showScreen(onboardingScreen);
            }
        });
    });

    // Set up close buttons for modals
    closeButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            // Find the closest modal or feedback panel
            const modal = button.closest('.modal');
            if (modal) {
                hideModal(modal);
            } else if (questionScreen.classList.contains('active')) {
                // If in question screen, go back to game options
                showScreen(gameOptionsScreen);
            }
        });
    });

    // Modal overlay close
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', () => {
            const modal = overlay.closest('.modal');
            if (modal) {
                hideModal(modal);
            }
        });
    });

    // Option selection in game options
    document.querySelectorAll('.option-button').forEach(button => {
        button.addEventListener('click', () => {
            // Find all sibling options
            const siblings = Array.from(button.parentElement.children);
            // Remove active class from all
            siblings.forEach(sib => sib.classList.remove('active'));
            // Add active to clicked button
            button.classList.add('active');
        });
    });

    // Answer selection in question screen
    document.querySelectorAll('.answer-option').forEach(option => {
        option.addEventListener('click', () => {
            document.querySelectorAll('.answer-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            option.classList.add('selected');
        });
    });

    // Question submit
    const submitButton = document.querySelector('#question-screen .primary-button');
    submitButton.addEventListener('click', () => {
        const feedbackPanel = document.getElementById('feedback-panel');
        feedbackPanel.classList.add('show');
    });

    // Feedback panel next button
    document.querySelector('#feedback-panel .primary-button').addEventListener('click', () => {
        const feedbackPanel = document.getElementById('feedback-panel');
        feedbackPanel.classList.remove('show');
    });

    // Category bubbles
    document.querySelectorAll('.category-bubble').forEach(bubble => {
        bubble.addEventListener('click', () => {
            document.querySelectorAll('.category-bubble').forEach(b => {
                b.classList.remove('active');
            });
            bubble.classList.add('active');
        });
    });
});