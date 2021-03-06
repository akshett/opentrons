// @flow
import React from 'react'
import cx from 'classnames'

import { wellIsRect, type WellDefinition } from '@opentrons/shared-data'
import styles from './Well.css'
import { SELECTABLE_WELL_CLASS } from '../constants.js'

export type SingleWell = {|
  wellName: string,
  highlighted?: ?boolean, // highlighted is the same as hovered
  selected?: ?boolean,
  error?: ?boolean,
  maxVolume?: number,
  fillColor?: ?string,
|}

export type WellProps = {|
  ...SingleWell,
  selectable?: boolean,
  wellDef: WellDefinition,
  onMouseOver?: (e: SyntheticMouseEvent<*>) => mixed,
  onMouseLeave?: (e: SyntheticMouseEvent<*>) => mixed,
  onMouseMove?: (e: SyntheticMouseEvent<*>) => mixed,
|}

export class Well extends React.Component<WellProps> {
  shouldComponentUpdate(nextProps: WellProps) {
    return (
      this.props.highlighted !== nextProps.highlighted ||
      this.props.selected !== nextProps.selected ||
      this.props.fillColor !== nextProps.fillColor
    )
  }
  render() {
    const {
      wellName,
      selectable,
      highlighted,
      selected,
      error,
      wellDef,
      onMouseOver,
      onMouseLeave,
      onMouseMove,
    } = this.props

    const fillColor = this.props.fillColor || 'transparent'

    const wellOverlayClassname = cx(styles.well_border, {
      [SELECTABLE_WELL_CLASS]: selectable,
      [styles.selected]: selected,
      [styles.selected_overlay]: selected,
      [styles.highlighted]: highlighted,
      [styles.error]: error,
    })

    const selectionProps = {
      'data-wellname': wellName,
      onMouseOver,
      onMouseLeave,
      onMouseMove,
    }

    const isRect = wellIsRect(wellDef)
    const isCircle = !isRect

    if (isRect) {
      const rectProps = {
        x: wellDef.x,
        y: wellDef.y,
        width: wellDef.width,
        height: wellDef.length,
      }

      return (
        <g>
          {/* Fill contents */}
          <rect {...rectProps} className={styles.well_fill} color={fillColor} />
          {/* Border + overlay */}
          <rect
            {...selectionProps}
            {...rectProps}
            className={wellOverlayClassname}
          />
        </g>
      )
    }

    if (isCircle) {
      const circleProps = {
        cx: wellDef.x,
        cy: wellDef.y,
        r: (wellDef.diameter || 0) / 2,
      }

      return (
        <g>
          {/* Fill contents */}
          <circle
            {...circleProps}
            className={styles.well_fill}
            color={fillColor}
          />
          {/* Border + overlay */}
          <circle
            {...selectionProps}
            {...circleProps}
            className={wellOverlayClassname}
          />
        </g>
      )
    }

    console.warn(
      'Invalid well: neither rectangle or circle: ' + JSON.stringify(wellDef)
    )
    return null
  }
}
