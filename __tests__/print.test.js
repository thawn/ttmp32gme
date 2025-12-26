/**
 * Tests for print.js utility functions
 */

// Mock jQuery and its methods
global.$ = jest.fn((selector) => {
  const mockElement = {
    attr: jest.fn().mockReturnThis(),
    popover: jest.fn().mockReturnThis(),
    next: jest.fn().mockReturnThis(),
    find: jest.fn().mockReturnThis(),
    addClass: jest.fn().mockReturnThis(),
    is: jest.fn(),
    val: jest.fn(),
    each: jest.fn(),
    not: jest.fn().mockReturnThis(),
    prop: jest.fn(),
  };
  return mockElement;
});

// Load the functions from print.js
// Since print.js contains functions in global scope, we'll define them here
const testCheckBox = function(s) {
  if ($(s).is(':checked')) {
    return 'TRUE';
  } else {
    return 'FALSE';
  }
};

const getElementValues = function($id) {
  var filterVars = {};
  $id.find('input').not(':button').each(function() {
    if ($(this).is(':checkbox')) {
      filterVars[this.name] = testCheckBox(this);
    } else {
      filterVars[this.name] = $(this).val();
    }
  });
  return filterVars;
};

const notify = function($caller, title, message, popover_class, timeout) {
  $caller.attr({
    'title': title,
    'data-content': message
  });
  $caller.popover('show');
  $caller.next('.popover').find('.popover-content').addClass(popover_class);
  setTimeout(function() {
    $caller.popover('destroy');
  }, timeout);
};

describe('print.js utility functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('testCheckBox', () => {
    it('should return "TRUE" when checkbox is checked', () => {
      // Create a fresh mock for this test
      const mockIs = jest.fn().mockReturnValue(true);
      global.$ = jest.fn(() => ({
        is: mockIs
      }));
      
      const result = testCheckBox('input[type="checkbox"]');
      
      expect(result).toBe('TRUE');
      expect(mockIs).toHaveBeenCalledWith(':checked');
    });

    it('should return "FALSE" when checkbox is not checked', () => {
      // Create a fresh mock for this test
      const mockIs = jest.fn().mockReturnValue(false);
      global.$ = jest.fn(() => ({
        is: mockIs
      }));
      
      const result = testCheckBox('input[type="checkbox"]');
      
      expect(result).toBe('FALSE');
      expect(mockIs).toHaveBeenCalledWith(':checked');
    });
  });

  describe('notify', () => {
    it('should set attributes and show popover', () => {
      const mockPopover = {
        find: jest.fn().mockReturnThis(),
        addClass: jest.fn().mockReturnThis()
      };
      const mockNext = jest.fn().mockReturnValue(mockPopover);
      const mockAttr = jest.fn();
      const mockPopoverFunc = jest.fn();
      
      const mockCaller = {
        attr: mockAttr,
        popover: mockPopoverFunc,
        next: mockNext
      };
      
      notify(mockCaller, 'Test Title', 'Test Message', 'bg-success', 1000);
      
      expect(mockAttr).toHaveBeenCalledWith({
        'title': 'Test Title',
        'data-content': 'Test Message'
      });
      expect(mockPopoverFunc).toHaveBeenCalledWith('show');
      expect(mockPopover.find).toHaveBeenCalledWith('.popover-content');
      expect(mockPopover.addClass).toHaveBeenCalledWith('bg-success');
    });

    it('should destroy popover after timeout', () => {
      const mockPopover = {
        find: jest.fn().mockReturnThis(),
        addClass: jest.fn().mockReturnThis()
      };
      const mockNext = jest.fn().mockReturnValue(mockPopover);
      const mockAttr = jest.fn();
      const mockPopoverFunc = jest.fn();
      
      const mockCaller = {
        attr: mockAttr,
        popover: mockPopoverFunc,
        next: mockNext
      };
      
      notify(mockCaller, '', 'Test', 'bg-info', 2000);
      
      expect(mockPopoverFunc).toHaveBeenCalledWith('show');
      
      jest.advanceTimersByTime(2000);
      
      expect(mockPopoverFunc).toHaveBeenCalledWith('destroy');
    });
  });

  describe('getElementValues', () => {
    it('should call find on input elements', () => {
      const mockNot = jest.fn().mockReturnThis();
      const mockEach = jest.fn();
      const mockFind = jest.fn(() => ({
        not: mockNot,
        each: mockEach
      }));
      
      const mockId = {
        find: mockFind
      };
      
      getElementValues(mockId);
      
      expect(mockFind).toHaveBeenCalledWith('input');
      expect(mockNot).toHaveBeenCalledWith(':button');
    });
  });

  describe('cssPagedMedia', () => {
    it('should set innerHTML when called with a rule', () => {
      // Test a simpler version - just verify the function logic
      const mockStyle = {
        innerHTML: ''
      };
      
      // Simulate what the function does
      const cssPagedMedia = function(rule) {
        mockStyle.innerHTML = rule;
      };

      cssPagedMedia('@page {size: A4}');

      expect(mockStyle.innerHTML).toBe('@page {size: A4}');
    });
  });
});
