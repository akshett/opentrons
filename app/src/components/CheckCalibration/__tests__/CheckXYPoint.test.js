// @flow
import * as React from 'react'
import { mount } from 'enzyme'
import { act } from 'react-dom/test-utils'
import type { Mount } from '@opentrons/components'

import { CheckXYPoint } from '../CheckXYPoint'

describe('CheckXYPoint', () => {
  let render

  const mockComparePoint = jest.fn()
  const mockGoToNextCheck = jest.fn()
  const mockJog = jest.fn()
  const mockExit = jest.fn()

  const getContinueButton = wrapper =>
    wrapper.find('PrimaryButton[children="continue"]').find('button')

  const getJogButton = (wrapper, direction) =>
    wrapper.find(`JogButton[name="${direction}"]`).find('button')

  const getVideo = wrapper => wrapper.find(`source`)

  beforeEach(() => {
    render = (props: $Shape<React.ElementProps<typeof CheckXYPoint>> = {}) => {
      const {
        slotNumber = '1',
        isMulti = false,
        mount: mountProp = 'left',
        isInspecting = false,
        comparison = {
          differenceVector: [0, 0, 0],
          thresholdVector: [1, 1, 1],
          exceedsThreshold: false,
        },
        nextButtonText = 'continue',
      } = props
      return mount(
        <CheckXYPoint
          slotNumber={slotNumber}
          isMulti={isMulti}
          mount={mountProp}
          isInspecting={isInspecting}
          comparison={comparison}
          nextButtonText={nextButtonText}
          exit={mockExit}
          comparePoint={mockComparePoint}
          goToNextCheck={mockGoToNextCheck}
          jog={mockJog}
        />
      )
    }
  })
  afterEach(() => {
    jest.resetAllMocks()
  })

  it('displays proper demo asset', () => {
    const slot1LeftMultiSrc = 'SLOT_1_LEFT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot1LeftSingleSrc = 'SLOT_1_LEFT_SINGLE_X-Y_(640X480)_REV1.webm'
    const slot1RightMultiSrc = 'SLOT_1_RIGHT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot1RightSingleSrc = 'SLOT_1_RIGHT_SINGLE_X-Y_(640X480)_REV1.webm'
    const slot3LeftMultiSrc = 'SLOT_3_LEFT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot3LeftSingleSrc = 'SLOT_3_LEFT_SINGLE_X-Y_(640X480)_REV1.webm'
    const slot3RightMultiSrc = 'SLOT_3_RIGHT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot3RightSingleSrc = 'SLOT_3_RIGHT_SINGLE_X-Y_(640X480)_REV1.webm'
    const slot7LeftMultiSrc = 'SLOT_7_LEFT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot7LeftSingleSrc = 'SLOT_7_LEFT_SINGLE_X-Y_(640X480)_REV1.webm'
    const slot7RightMultiSrc = 'SLOT_7_RIGHT_MULTI_X-Y_(640X480)_REV1.webm'
    const slot7RightSingleSrc = 'SLOT_7_RIGHT_SINGLE_X-Y_(640X480)_REV1.webm'
    const assetMap: { [string]: { [Mount]: { ... }, ... }, ... } = {
      '1': {
        left: {
          multi: slot1LeftMultiSrc,
          single: slot1LeftSingleSrc,
        },
        right: {
          multi: slot1RightMultiSrc,
          single: slot1RightSingleSrc,
        },
      },
      '3': {
        left: {
          multi: slot3LeftMultiSrc,
          single: slot3LeftSingleSrc,
        },
        right: {
          multi: slot3RightMultiSrc,
          single: slot3RightSingleSrc,
        },
      },
      '7': {
        left: {
          multi: slot7LeftMultiSrc,
          single: slot7LeftSingleSrc,
        },
        right: {
          multi: slot7RightMultiSrc,
          single: slot7RightSingleSrc,
        },
      },
    }
    Object.keys(assetMap).forEach(slotNumber => {
      const xyStep = assetMap[slotNumber]
      Object.keys(xyStep).forEach(mountString => {
        Object.keys(xyStep[mountString]).forEach(channelString => {
          const wrapper = render({
            mount: mountString,
            isMulti: channelString === 'multi',
            slotNumber: slotNumber,
          })
          expect(getVideo(wrapper).prop('src')).toEqual(
            xyStep[mountString][channelString]
          )
        })
      })
    })
  })

  it('allows jogging in x and y axis', () => {
    const wrapper = render()

    const jogDirections = ['left', 'right', 'back', 'forward']
    const jogParamsByDirection = {
      left: ['x', -1, 0.1],
      right: ['x', 1, 0.1],
      back: ['y', 1, 0.1],
      forward: ['y', -1, 0.1],
    }
    jogDirections.forEach(direction => {
      act(() => getJogButton(wrapper, direction).invoke('onClick')())
      wrapper.update()

      expect(mockJog).toHaveBeenCalledWith(...jogParamsByDirection[direction])
    })

    const unavailableJogDirections = ['up', 'down']
    unavailableJogDirections.forEach(direction => {
      expect(getJogButton(wrapper, direction)).toEqual({})
    })
  })

  it('compares check step when primary button is clicked', () => {
    const wrapper = render()

    act(() => getContinueButton(wrapper).invoke('onClick')())
    wrapper.update()

    expect(mockComparePoint).toHaveBeenCalled()
  })

  it('confirms check step when isInspecting and primary button is clicked', () => {
    const wrapper = render({ isInspecting: true })

    act(() => getContinueButton(wrapper).invoke('onClick')())
    wrapper.update()

    expect(mockGoToNextCheck).toHaveBeenCalled()
  })
})
