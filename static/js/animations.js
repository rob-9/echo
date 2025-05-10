// Typing animation configuration
const config = {
    text: "Reduce designer-client back-and-forths with smart, streamlined project briefs.",
    typingSpeed: 25,  // Speed in milliseconds between each character
    startDelay: 500,  // Delay before starting the animation in milliseconds
    cursor: "|",      // Cursor character
    cursorSpeed: 500  // Cursor blink speed in milliseconds
};

// Typing animation function
function typeText() {
    const element = document.getElementById('typing-text');
    let text = '';
    let cursorVisible = true;
    
    // Add cursor
    function updateCursor() {
        if (cursorVisible) {
            element.textContent = text + config.cursor;
        } else {
            element.textContent = text;
        }
        cursorVisible = !cursorVisible;
    }

    // Start cursor blinking
    const cursorInterval = setInterval(updateCursor, config.cursorSpeed);

    // Type the text
    let i = 0;
    const typingInterval = setInterval(() => {
        if (i < config.text.length) {
            text += config.text[i];
            element.textContent = text + (cursorVisible ? config.cursor : '');
            i++;
        } else {
            clearInterval(typingInterval);
            clearInterval(cursorInterval);
            element.textContent = text; // Remove cursor when done
        }
    }, config.typingSpeed);
}

// Start the animation after the specified delay
setTimeout(typeText, config.startDelay);

// Add cursor-following border effect
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.category-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Calculate distance from cursor to card edges
            const distanceFromLeft = x;
            const distanceFromRight = rect.width - x;
            const distanceFromTop = y;
            const distanceFromBottom = rect.height - y;
            
            // Find the closest edge
            const minDistance = Math.min(distanceFromLeft, distanceFromRight, distanceFromTop, distanceFromBottom);
            
            if (minDistance < 20) { // If cursor is within 20px of any edge
                card.style.setProperty('--border-opacity', '1');
            } else {
                card.style.setProperty('--border-opacity', '0');
            }
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.setProperty('--border-opacity', '0');
        });
    });
}); 